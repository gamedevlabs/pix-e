from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
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
