from django.http import HttpResponse, JsonResponse
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import SessionAuthentication

from .gemini.GeminiLink import GeminiLink
from .models import GameDesignDescription, Pillar
from .serializers import GameDesignSerializer, PillarSerializer
from django.shortcuts import render
from django.views import View
from rest_framework import status
import uuid
from diffusers import StableDiffusionPipeline, StableDiffusionOnnxPipeline
import torch
import os
import webcolors
from .services.manager import llm_manager
from .services.base import LLMServiceError
import threading
import time
import logging

# Create your views here.

logger = logging.getLogger(__name__)


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Session authentication that doesn't enforce CSRF for API calls"""

    def enforce_csrf(self, request):
        return  # Skip CSRF check


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
                provider=["CUDAExecutionProvider", "CPUExecutionProvider"],
            )
        except Exception:
            # Fallback to normal pipeline if ONNX is not available
            sd_model = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16
            )
            sd_model = sd_model.to("cuda")
    return sd_model


# Placeholder for Stable Diffusion image generation
def generate_gaming_images(prompt, num_images=3):
    """
    Generate gaming-themed images using Stable Diffusion
    Falls back to placeholder images if SD is not available
    """
    try:
        # Try to use Stable Diffusion
        pipe = get_sd_model()
        # Disable NSFW filter if possible
        if hasattr(pipe, "safety_checker"):
            pipe.safety_checker = None
        images = pipe(
            [prompt] * num_images, num_inference_steps=30, height=512, width=512
        ).images

        # Save generated images
        import uuid, os
        from django.conf import settings

        image_urls = []
        for img in images:
            img_id = str(uuid.uuid4())
            img_path = os.path.join(
                settings.BASE_DIR, "media", f"moodboard_{img_id}.png"
            )
            os.makedirs(os.path.dirname(img_path), exist_ok=True)
            img.save(img_path)
            image_urls.append(f"/media/moodboard_{img_id}.png")
        return image_urls

    except Exception as e:
        # Stable Diffusion not available, using placeholder images
        # Create placeholder images for testing
        import uuid, os
        from PIL import Image, ImageDraw, ImageFont
        from django.conf import settings

        image_urls = []
        for i in range(num_images):
            # Create a simple placeholder image
            img = Image.new("RGB", (512, 512), color=(73, 109, 137))
            draw = ImageDraw.Draw(img)

            # Add text
            text_lines = [
                f"Generated Image {i+1}",
                f"Prompt: {prompt[:30]}{'...' if len(prompt) > 30 else ''}",
                "Placeholder Image",
            ]

            y_pos = 200
            for line in text_lines:
                # Use default font
                try:
                    font = ImageFont.load_default()
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    draw.text(
                        (256 - text_width // 2, y_pos),
                        line,
                        fill=(255, 255, 255),
                        font=font,
                    )
                except:
                    # Fallback without font
                    draw.text((100, y_pos), line, fill=(255, 255, 255))
                y_pos += 30

            # Save the image
            img_id = str(uuid.uuid4())
            img_path = os.path.join(
                settings.BASE_DIR, "media", f"moodboard_{img_id}.png"
            )
            os.makedirs(os.path.dirname(img_path), exist_ok=True)
            img.save(img_path)
            image_urls.append(f"/media/moodboard_{img_id}.png")

        return image_urls


# Legacy moodboard API views removed - now using moodboards app with REST API structure
# Kept only the image generation utilities that may be used by the new API


class TextSuggestionView(APIView):
    """API for getting text suggestions from LLM models"""

    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get available LLM services and their status"""
        try:
            services = llm_manager.list_services()
            active_service = llm_manager.get_active_service()

            return JsonResponse(
                {
                    "services": services,
                    "active_service": active_service,
                    "status": "success",
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e), "status": "error"}, status=500)

    def post(self, request):
        """Generate text suggestions based on prompt"""
        try:
            # Use DRF request.data for consistent parsing
            data = request.data

            prompt = data.get("prompt", "").strip()
            service_id = data.get("service_id") or data.get(
                "service"
            )  # Check both 'service_id' and 'service' for compatibility
            mode = data.get("mode", "default").lower()  # Get mode (gaming/default)
            suggestion_type = data.get(
                "suggestion_type", "short"
            ).lower()  # Get suggestion length preference
            num_suggestions = min(
                int(data.get("num_suggestions", 3)), 5
            )  # Max 5 suggestions

            if not prompt:
                return JsonResponse(
                    {"error": "Prompt is required", "status": "error"}, status=400
                )

            if len(prompt) < 3:
                return JsonResponse(
                    {
                        "error": "Prompt must be at least 3 characters long",
                        "status": "error",
                    },
                    status=400,
                )
            # Generate suggestions with context
            suggestions = llm_manager.get_suggestions(
                prompt=prompt,
                service_id=service_id,
                num_suggestions=num_suggestions,
                mode=mode,
                suggestion_type=suggestion_type,
                temperature=0.8,
                user=request.user,  # Pass user for token authentication
            )

            return JsonResponse(
                {
                    "suggestions": suggestions,
                    "prompt": prompt,
                    "service_used": service_id or llm_manager.get_active_service(),
                    "status": "success",
                }
            )

        except LLMServiceError as e:
            return JsonResponse({"error": str(e), "status": "error"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"error": f"Internal server error: {str(e)}", "status": "error"},
                status=500,
            )


class LLMServiceManagementView(APIView):
    """API for managing LLM services (load/unload models)"""

    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Load or unload an LLM service"""
        try:
            # Handle JSON parsing
            if hasattr(request, "data") and request.data:
                data = request.data
            else:
                import json

                data = json.loads(request.body)

            action = data.get("action")  # 'load' or 'unload'
            service_id = data.get("service_id")
            model_name = data.get("model_name")

            if not service_id:
                return JsonResponse(
                    {"error": "service_id is required", "status": "error"}, status=400
                )

            if action == "load":
                success = llm_manager.load_service(service_id, model_name)
                if success:
                    status = llm_manager.get_service_status(service_id)
                    return JsonResponse(
                        {
                            "message": f"Service {service_id} loaded successfully",
                            "service_status": status,
                            "status": "success",
                        }
                    )
                else:
                    return JsonResponse(
                        {
                            "error": f"Failed to load service {service_id}",
                            "status": "error",
                        },
                        status=500,
                    )

            elif action == "unload":
                success = llm_manager.unload_service(service_id)
                if success:
                    return JsonResponse(
                        {
                            "message": f"Service {service_id} unloaded successfully",
                            "status": "success",
                        }
                    )
                else:
                    return JsonResponse(
                        {
                            "error": f"Failed to unload service {service_id}",
                            "status": "error",
                        },
                        status=500,
                    )

            else:
                return JsonResponse(
                    {
                        "error": 'Invalid action. Use "load" or "unload"',
                        "status": "error",
                    },
                    status=400,
                )

        except LLMServiceError as e:
            return JsonResponse({"error": str(e), "status": "error"}, status=400)
        except Exception as e:
            return JsonResponse(
                {"error": f"Internal server error: {str(e)}", "status": "error"},
                status=500,
            )

    def get(self, request):
        """Get detailed status of all services"""
        try:
            services = llm_manager.list_services()
            active_service = llm_manager.get_active_service()

            # Get detailed status for each service
            detailed_status = {}
            for service_id in services.keys():
                detailed_status[service_id] = llm_manager.get_service_status(service_id)

            return JsonResponse(
                {
                    "services": services,
                    "detailed_status": detailed_status,
                    "active_service": active_service,
                    "status": "success",
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e), "status": "error"}, status=500)
