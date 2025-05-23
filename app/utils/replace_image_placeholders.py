# import os
# import re
# from PIL import Image

# def replace_image_placeholders(
#     text, 
#     image_dir="/data/static/images", 
#     markdown=True, 
#     missing_policy="warn",
#     pillow=False
# ):
#     """
#     Replace [image_name.png] with Markdown or HTML image references.
#     - markdown: if True, output ![image_name](/images/image_name.png), else <img ...>
#     - missing_policy: 'warn' replaces missing with '[Missing image: ...]', 'skip' removes the tag
#     """
#     imgs = []
#     def replacer(match):
#         filename = match.group(1)
#         filepath = os.path.join(image_dir, filename)
#         # Check file exists (optional for fallback)
#         if not os.path.isfile(filepath):
#             if missing_policy == "warn":
#                 return f"[Missing image: {filename}]"
#             elif missing_policy == "skip":
#                 return ""
#         if markdown:
#             imgs.append(filename)
#             if pillow:
#                 try:
#                     filepath = os.path.join(image_dir, filename)
#                     img = Image.open(filepath) # Replace "image.jpg" with the actual path
#                     img.show() # Displays the image
#                 except FileNotFoundError:
#                     print("Image file not found")
#                 except Exception as e:
#                     print(f"Error opening image: {e}")
        
#             return f"![{filename}](\/images\/{filename})"
#         else:
#             return f'<img src="/images/{filename}" alt="{filename}" style="max-width:100%;"/>'
#     pattern = r"\[([\w\-]+\.(?:png|jpg|jpeg|gif))\]"
#     return re.sub(pattern, replacer, text), imgs

# # Example usage
# text = "I want to show you this image: [teste.png] and this one: [missing_image.png]."
# image_dir = "data/static/images"
# text, imgs = replace_image_placeholders(text, image_dir, markdown=True, missing_policy="warn", pillow=True)
# print(text)
# print(imgs)