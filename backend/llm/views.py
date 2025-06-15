# from django.shortcuts import render
# from django.views import View
# from rest_framework.views import APIView

from django.http import HttpResponse, JsonResponse
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .gemini.GeminiLink import GeminiLink
from .models import GameDesignDescription, Pillar
from .serializers import GameDesignSerializer, PillarSerializer
from django.shortcuts import render
from django.views import View
from rest_framework import status
from .models import MoodboardSession, MoodboardImage
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
import uuid
from diffusers import StableDiffusionPipeline, StableDiffusionOnnxPipeline
import torch
import requests
import os
import webcolors
# Create your views here.


class PillarViewSet(ModelViewSet):
    serializer_class = PillarSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pillar_id"

    def get_queryset(self):
        return Pillar.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DesignView(ModelViewSet):
    serializer_class = GameDesignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GameDesignDescription.objects.filter(user=self.request.user)

    def get_object(self):
        return GameDesignDescription.objects.get(user=self.request.user)

    @action(detail=False, methods=["GET"], url_path="get_or_create")
    def get_or_create(self, request):
        obj, created = GameDesignDescription.objects.get_or_create(
            user=self.request.user, defaults={"description": ""}
        )
        serializer = self.get_serializer(obj)
        return Response(
            serializer.data,
            status=201 if created else 200,
        )


class OverallFeedbackView(APIView):
    def __init__(self, **kwargs):
        super().__init__()
        self.gemini = GeminiLink()

    def get(self, request):
        try:
            design = GameDesignDescription.objects.first()
            pillars = [pillar for pillar in Pillar.objects.all()]

            prompt = (
                f"Rate the following game design description with regards to the "
                f"following design pillars:\n"
                f"{design}\n\nPillars:\n"
            )
            prompt += f"Game Design Description: {design.description}\n"
            prompt += "Design Pillars:\n"
            for pillar in pillars:
                prompt += f"Title: {pillar.title}\n"
                prompt += f"Description: {pillar.description}\n\n"

            prompt += (
                "\nDo not use any markdown in your answer. Answer directly as "
                "if you are giving your feedback to "
                "the designer."
            )
            answer = self.gemini.generate_response(prompt)
            return JsonResponse({"feedback": answer}, status=200)
        except Exception as e:
            return HttpResponse({"error": str(e)}, status=404)


class PillarFeedbackView(APIView):
    def __init__(self, **kwargs):
        super().__init__()
        self.gemini = GeminiLink()

    def get(self, request, pillar_id):
        try:
            pillar = Pillar.objects.filter(pillar_id=pillar_id).first()
            prompt = """Check if the following Game Design Pillar is written in a
                        sensible way. First validate, but only list these issues if
                        they are present otherwise ignore this section:
                        1. The title is not clear or does not match the description.
                        2. The description is not written as continuous text.
                        3. The intent of the pillar is not clear.\n
                        Then give feedback on the pillar and if it could be improved.\n
                      \n\n"""
            prompt += f"Title: {pillar.title}\n"
            prompt += f"Description: {pillar.description}\n\n"

            prompt += (
                "Do not use any markdown in your answer. Answer directly as if"
                " your giving your feedback to the "
                "designer."
            )
            answer = self.gemini.generate_response(prompt)
            return JsonResponse({"feedback": answer}, status=200)
        except Exception as e:
            return HttpResponse({"error": e}, status=404)


# Load Stable Diffusion model once (for demo, use CPU; for production, use GPU if available)
sd_model = None
def get_sd_model():
    global sd_model
    if sd_model is None:
        try:
            # Try ONNX pipeline for much faster inference (GPU-friendly)
            sd_model = StableDiffusionOnnxPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                provider=["CUDAExecutionProvider", "CPUExecutionProvider"]
            )
        except Exception:
            # Fallback to normal pipeline if ONNX is not available
            sd_model = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float16
            )
            sd_model = sd_model.to("cuda")
    return sd_model

# Placeholder for Stable Diffusion image generation
def generate_gaming_images(prompt, num_images=3):
    # Only use the user's prompt for relevance
    full_prompt = prompt
    pipe = get_sd_model()
    # Disable NSFW filter if possible
    if hasattr(pipe, 'safety_checker'):
        pipe.safety_checker = None
    images = pipe(
        [full_prompt] * num_images,
        num_inference_steps=30,
        height=512,
        width=512
    ).images
    import uuid, os
    from django.conf import settings
    image_urls = []
    for img in images:
        img_id = str(uuid.uuid4())
        img_path = os.path.join(settings.BASE_DIR, 'media', f"moodboard_{img_id}.png")
        os.makedirs(os.path.dirname(img_path), exist_ok=True)
        img.save(img_path)
        image_urls.append(f"/media/moodboard_{img_id}.png")
    return image_urls

def summarize_palette(hex_list):
    names = []
    for hex_code in hex_list:
        try:
            name = webcolors.hex_to_name(hex_code)
        except ValueError:
            try:
                rgb = webcolors.hex_to_rgb(hex_code)
                name = webcolors.rgb_to_name(rgb)
            except Exception:
                # Fallback: use short hex or just the color
                name = hex_code.lstrip('#').upper()
        names.append(name.replace('_', ' '))
    return ', '.join(names)

class MoodboardStartView(APIView):
    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        session = MoodboardSession.objects.create(user=user)
        return Response({"session_id": str(session.id)}, status=status.HTTP_201_CREATED)

class MoodboardGenerateView(APIView):
    def post(self, request):
        session_id = request.data.get("session_id")
        prompt = request.data.get("prompt")
        selected_image_ids = request.data.get("selected_image_ids", [])
        mode = request.data.get("mode", "default")
        session = get_object_or_404(MoodboardSession, id=session_id, is_active=True)

        # Mark selected images
        if selected_image_ids:
            MoodboardImage.objects.filter(id__in=selected_image_ids, session=session).update(is_selected=True)

        # Extract color palette from prompt if present
        color_palette = None
        if ", color palette:" in prompt:
            parts = prompt.split(", color palette:")
            prompt_main = parts[0].strip()
            color_palette = parts[1].strip()
        else:
            prompt_main = prompt

        # Compose prompt with palette and mood/style at the start
        palette_instruction = ""
        if color_palette:
            # Try to parse hex codes and summarize
            hex_list = [c.strip() for c in color_palette.split(',') if c.strip().startswith('#')]
            if hex_list:
                palette_names = summarize_palette(hex_list)
                palette_instruction = f"Color palette: {palette_names}. "
            else:
                # fallback: use as-is
                palette_instruction = f"Color palette: {color_palette}. "
        if mode == "gaming":
            game_prefix = (
                "Concept art for a game environment. The scene should reflect the atmosphere, mood, and style described in the prompt, which could be realistic, stylized, dark, bright, whimsical, or any other game world. Do not restrict to only virtual or typical game settings. "
            )
            full_prompt = f"{palette_instruction}{game_prefix}{prompt_main}"
        else:
            full_prompt = f"{palette_instruction}{prompt_main}"

        images = generate_gaming_images(full_prompt)
        image_objs = [MoodboardImage.objects.create(session=session, image_url=url, prompt=prompt) for url in images]

        # Only delete images that are not selected and are not from the current prompt (i.e., not newly generated)
        MoodboardImage.objects.filter(session=session, is_selected=False).exclude(prompt=prompt).delete()

        # Always return all unselected images (for selection) and all selected images (for moodboard)
        images_unselected = session.images.filter(is_selected=False)
        moodboard = session.images.filter(is_selected=True)

        return Response({
            "images": [
                {"id": img.id, "url": img.image_url, "prompt": img.prompt, "is_selected": img.is_selected}
                for img in images_unselected
            ],
            "moodboard": [
                {"id": img.id, "url": img.image_url, "prompt": img.prompt, "is_selected": img.is_selected}
                for img in moodboard
            ]
        }, status=status.HTTP_200_OK)

class MoodboardGetView(APIView):
    def get(self, request, session_id):
        session = get_object_or_404(MoodboardSession, id=session_id)
        images = session.images.filter(is_selected=False)
        moodboard = session.images.filter(is_selected=True)
        return Response({
            "session_id": str(session.id),
            "images": [
                {"id": img.id, "url": img.image_url, "prompt": img.prompt, "is_selected": img.is_selected}
                for img in images
            ],
            "moodboard": [
                {"id": img.id, "url": img.image_url, "prompt": img.prompt, "is_selected": img.is_selected}
                for img in moodboard
            ],
            "is_active": session.is_active
        })

class MoodboardEndView(APIView):
    def post(self, request):
        session_id = request.data.get("session_id")
        selected_image_ids = request.data.get("selected_image_ids", [])
        session = get_object_or_404(MoodboardSession, id=session_id, is_active=True)
        # Mark selected images from the last step
        if selected_image_ids:
            MoodboardImage.objects.filter(id__in=selected_image_ids, session=session).update(is_selected=True)
        session.is_active = False
        session.save()
        # Return the final moodboard
        moodboard = session.images.filter(is_selected=True)
        return Response({
            "message": "Moodboard session ended.",
            "moodboard": [
                {"id": img.id, "url": img.image_url, "prompt": img.prompt, "is_selected": img.is_selected}
                for img in moodboard
            ]
        }, status=status.HTTP_200_OK)

class MoodboardSuggestView(APIView):
    def post(self, request):
        prompt = request.data.get("prompt", "")
        # Use local Ollama server for open-source LLM inference
        # OLLAMA_API_URL = "http://localhost:11434/api/generate"
        # system_prompt = (
        #     "You are an expert game environment concept artist. "
        #     "Given a partial or full prompt, suggest 3 creative, relevant, and visually distinct prompt refinements "
        #     "for generating moodboard images. Only return the suggestions as a numbered list."
        # )
        # user_prompt = f"{prompt}"
        # payload = {
        #     "model": "llama3",  # Change to your preferred model if needed
        #     "prompt": f"{system_prompt}\nPrompt: {user_prompt}\nSuggestions:",
        #     "stream": False
        # }
        # try:
        #     response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        #     data = response.json()
        #     text = data.get("response", "")
        #     # Parse numbered list
        #     suggestions = [s.strip(" .-") for s in text.split("\n") if s.strip() and any(c.isalpha() for s in s)]
        #     suggestions = [s.split(".", 1)[-1].strip() if s[0].isdigit() else s for s in suggestions]
        #     return Response({"suggestions": suggestions[:3]})
        # except Exception as e:
        #     return Response({"error": str(e)}, status=500)
        return Response({"suggestions": []})
