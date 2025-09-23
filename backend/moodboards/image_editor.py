"""
Image editing utilities for moodboard images.
Provides functionality to apply filters, crop, rotate, and adjust images.
"""

import io
import os
import base64
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import uuid


class ImageEditor:
    """Handle image editing operations for moodboard images"""
    
    SUPPORTED_FORMATS = ['JPEG', 'PNG', 'WEBP']
    MAX_IMAGE_SIZE = (2048, 2048)  # Max dimensions
    
    def __init__(self, image_path: str):
        """Initialize with image path"""
        self.image_path = image_path
        self.image = None
        self.load_image()
    
    def load_image(self):
        """Load image from storage or absolute path"""
        try:
            # Check if it's an absolute path (for testing) or relative path (for production)
            if os.path.isabs(self.image_path):
                # Direct file path - used for testing
                with open(self.image_path, 'rb') as img_file:
                    self.image = Image.open(img_file).copy()
            else:
                # Django storage path - used in production
                if default_storage.exists(self.image_path):
                    with default_storage.open(self.image_path, 'rb') as img_file:
                        self.image = Image.open(img_file).copy()
                else:
                    raise FileNotFoundError(f"Image not found: {self.image_path}")
            
            # Convert to RGB if necessary
            if self.image.mode in ('RGBA', 'LA', 'P'):
                # Create a white background for transparency
                background = Image.new('RGB', self.image.size, (255, 255, 255))
                if self.image.mode == 'P':
                    self.image = self.image.convert('RGBA')
                if self.image.mode in ('RGBA', 'LA'):
                    background.paste(self.image, mask=self.image.split()[-1])
                    self.image = background
        except Exception as e:
            raise Exception(f"Failed to load image: {str(e)}")
    
    def apply_filter(self, filter_name: str, intensity: float = 1.0) -> 'ImageEditor':
        """Apply image filter"""
        if not self.image:
            raise ValueError("No image loaded")
        
        intensity = max(0.0, min(1.0, intensity))  # Clamp between 0 and 1
        
        if filter_name == 'blur':
            # Apply Gaussian blur
            radius = intensity * 5  # Max blur radius of 5
            self.image = self.image.filter(ImageFilter.GaussianBlur(radius=radius))
            
        elif filter_name == 'sharpen':
            # Apply sharpening
            if intensity > 0:
                filter_obj = ImageFilter.UnsharpMask(radius=2, percent=int(intensity * 150), threshold=3)
                self.image = self.image.filter(filter_obj)
                
        elif filter_name == 'edge_enhance':
            # Edge enhancement
            if intensity > 0:
                enhanced = self.image.filter(ImageFilter.EDGE_ENHANCE_MORE)
                self.image = Image.blend(self.image, enhanced, intensity)
                
        elif filter_name == 'emboss':
            # Emboss effect
            if intensity > 0:
                embossed = self.image.filter(ImageFilter.EMBOSS)
                self.image = Image.blend(self.image, embossed, intensity)
                
        elif filter_name == 'sepia':
            # Sepia tone effect
            if intensity > 0:
                # Convert to grayscale first
                grayscale = ImageOps.grayscale(self.image)
                # Apply sepia tint
                sepia = ImageOps.colorize(grayscale, "#704214", "#C0A882")
                self.image = Image.blend(self.image, sepia, intensity)
                
        elif filter_name == 'vintage':
            # Vintage effect (combination of sepia and slight blur)
            if intensity > 0:
                # Slight blur
                blurred = self.image.filter(ImageFilter.GaussianBlur(radius=0.5))
                # Sepia tone
                grayscale = ImageOps.grayscale(blurred)
                sepia = ImageOps.colorize(grayscale, "#8B4513", "#DEB887")
                # Reduce saturation
                enhancer = ImageEnhance.Color(sepia)
                vintage = enhancer.enhance(0.8)
                self.image = Image.blend(self.image, vintage, intensity)
        
        return self
    
    def adjust_brightness(self, factor: float) -> 'ImageEditor':
        """Adjust image brightness. Factor: 0.0-2.0 (1.0 = no change)"""
        if not self.image:
            raise ValueError("No image loaded")
        
        factor = max(0.0, min(2.0, factor))
        enhancer = ImageEnhance.Brightness(self.image)
        self.image = enhancer.enhance(factor)
        return self
    
    def adjust_contrast(self, factor: float) -> 'ImageEditor':
        """Adjust image contrast. Factor: 0.0-2.0 (1.0 = no change)"""
        if not self.image:
            raise ValueError("No image loaded")
        
        factor = max(0.0, min(2.0, factor))
        enhancer = ImageEnhance.Contrast(self.image)
        self.image = enhancer.enhance(factor)
        return self
    
    def adjust_saturation(self, factor: float) -> 'ImageEditor':
        """Adjust image saturation. Factor: 0.0-2.0 (1.0 = no change)"""
        if not self.image:
            raise ValueError("No image loaded")
        
        factor = max(0.0, min(2.0, factor))
        enhancer = ImageEnhance.Color(self.image)
        self.image = enhancer.enhance(factor)
        return self
    
    def rotate(self, angle: float) -> 'ImageEditor':
        """Rotate image by angle in degrees"""
        if not self.image:
            raise ValueError("No image loaded")
        
        # Normalize angle to 0-360 range
        angle = angle % 360
        self.image = self.image.rotate(angle, expand=True, fillcolor='white')
        return self
    
    def crop(self, x: int, y: int, width: int, height: int) -> 'ImageEditor':
        """Crop image to specified rectangle"""
        if not self.image:
            raise ValueError("No image loaded")
        
        # Ensure crop coordinates are within image bounds
        img_width, img_height = self.image.size
        x = max(0, min(x, img_width))
        y = max(0, min(y, img_height))
        width = max(1, min(width, img_width - x))
        height = max(1, min(height, img_height - y))
        
        crop_box = (x, y, x + width, y + height)
        self.image = self.image.crop(crop_box)
        return self
    
    def resize(self, width: int, height: int, maintain_aspect: bool = True) -> 'ImageEditor':
        """Resize image to specified dimensions"""
        if not self.image:
            raise ValueError("No image loaded")
        
        if maintain_aspect:
            self.image.thumbnail((width, height), Image.Resampling.LANCZOS)
        else:
            self.image = self.image.resize((width, height), Image.Resampling.LANCZOS)
        return self
    
    def flip_horizontal(self) -> 'ImageEditor':
        """Flip image horizontally"""
        if not self.image:
            raise ValueError("No image loaded")
        
        self.image = self.image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        return self
    
    def flip_vertical(self) -> 'ImageEditor':
        """Flip image vertically"""
        if not self.image:
            raise ValueError("No image loaded")
        
        self.image = self.image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        return self
    
    def save_edited_image(self, original_filename: str) -> str:
        """Save the edited image and return the new file path"""
        if not self.image:
            raise ValueError("No image to save")
        
        # Generate new filename with edited suffix
        file_extension = original_filename.split('.')[-1].lower()
        if file_extension not in ['jpg', 'jpeg', 'png', 'webp']:
            file_extension = 'jpg'
        
        new_filename = f"moodboard_edited_{uuid.uuid4().hex}.{file_extension}"
        
        # Convert image to bytes
        output = io.BytesIO()
        
        # Ensure image is in RGB mode for JPEG
        if file_extension in ['jpg', 'jpeg'] and self.image.mode != 'RGB':
            save_image = self.image.convert('RGB')
        else:
            save_image = self.image
        
        # Save with appropriate format
        format_map = {
            'jpg': 'JPEG',
            'jpeg': 'JPEG',
            'png': 'PNG',
            'webp': 'WEBP'
        }
        
        save_image.save(output, format=format_map[file_extension], quality=95, optimize=True)
        output.seek(0)
        
        # Save to storage
        file_content = ContentFile(output.getvalue())
        file_path = default_storage.save(new_filename, file_content)
        
        return file_path
    
    def get_image_info(self) -> Dict[str, Any]:
        """Get information about the current image"""
        if not self.image:
            return {}
        
        return {
            'width': self.image.size[0],
            'height': self.image.size[1],
            'mode': self.image.mode,
            'format': self.image.format or 'Unknown'
        }
    
    def to_base64(self) -> str:
        """Convert current image to base64 string for preview"""
        if not self.image:
            raise ValueError("No image loaded")
        
        output = io.BytesIO()
        
        # Convert to RGB if necessary for JPEG output
        if self.image.mode != 'RGB':
            preview_image = self.image.convert('RGB')
        else:
            preview_image = self.image
        
        # Resize for preview if too large
        preview_image.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        preview_image.save(output, format='JPEG', quality=85)
        output.seek(0)
        
        return base64.b64encode(output.getvalue()).decode('utf-8')


def apply_batch_edits(image_path: str, edits: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Apply a batch of edits to an image and return the new image path and info.
    
    Args:
        image_path: Path to the original image
        edits: Dictionary containing edit operations and parameters
        
    Returns:
        Tuple of (new_image_path, image_info)
    """
    editor = ImageEditor(image_path)
    
    # Apply edits in order
    edit_order = [
        'crop', 'rotate', 'resize', 'flip_horizontal', 'flip_vertical',
        'brightness', 'contrast', 'saturation', 'filters'
    ]
    
    for edit_type in edit_order:
        if edit_type not in edits:
            continue
            
        if edit_type == 'crop' and edits['crop']:
            crop_data = edits['crop']
            editor.crop(
                crop_data.get('x', 0),
                crop_data.get('y', 0),
                crop_data.get('width', editor.image.size[0]),
                crop_data.get('height', editor.image.size[1])
            )
            
        elif edit_type == 'rotate' and edits['rotate']:
            try:
                rotate_value = float(edits['rotate'])
                if rotate_value != 0:  # Only rotate if not zero
                    editor.rotate(rotate_value)
            except (ValueError, TypeError):
                pass
            
        elif edit_type == 'resize' and edits['resize']:
            resize_data = edits['resize']
            editor.resize(
                resize_data.get('width', editor.image.size[0]),
                resize_data.get('height', editor.image.size[1]),
                resize_data.get('maintain_aspect', True)
            )
            
        elif edit_type == 'flip_horizontal' and edits.get('flip_horizontal'):
            editor.flip_horizontal()
            
        elif edit_type == 'flip_vertical' and edits.get('flip_vertical'):
            editor.flip_vertical()
            
        elif edit_type == 'brightness' and 'brightness' in edits:
            try:
                brightness_value = float(edits['brightness'])
                editor.adjust_brightness(brightness_value)
            except (ValueError, TypeError):
                pass
            
        elif edit_type == 'contrast' and 'contrast' in edits:
            try:
                contrast_value = float(edits['contrast'])
                editor.adjust_contrast(contrast_value)
            except (ValueError, TypeError):
                pass
            
        elif edit_type == 'saturation' and 'saturation' in edits:
            try:
                saturation_value = float(edits['saturation'])
                editor.adjust_saturation(saturation_value)
            except (ValueError, TypeError):
                pass
            
        elif edit_type == 'filters' and edits.get('filters'):
            filters = edits['filters']
            for filter_name, intensity in filters.items():
                try:
                    intensity_value = float(intensity)
                    if intensity_value > 0:
                        editor.apply_filter(filter_name, intensity_value)
                except (ValueError, TypeError):
                    pass
    
    # Save the edited image
    original_filename = image_path.split('/')[-1]
    new_image_path = editor.save_edited_image(original_filename)
    
    return new_image_path, editor.get_image_info()
