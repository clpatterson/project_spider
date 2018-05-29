import base64
import io
import math
from PIL import Image

def long_slice():
	"""slice an image into parts slice_size tall"""
	
	img = Image.open('/Users/Charlie/Desktop/test_image.png')
	width, height = img.size
	upper = 0
	left = 0
	
	# Max height to fit pdf.
	max_height_mm = 267
	max_height = (max_height_mm * 96) / 25.4

	slice_size = max_height

	# Calculate number of slices needed.
	slices = int(math.ceil(height/slice_size))
	count = 1

	final_slices = []
	for slice in range(slices):
		# If at the end, set the lower bound as bottom of the image.
		if count == slices:
			lower = height
		else:
			lower = int(count * slice_size)  
		# Set the bounding box.     
		bbox = (left, upper, width, lower)
		working_slice = img.crop(bbox)
		working_slice.show()

		# Save png as bytes object.
		byte_io = io.BytesIO()
		working_slice.save(byte_io, 'png')
		# Convert bytes object to base64 string and save to list.
		img_str = base64.b64encode(byte_io.getvalue())
		img_str = 'data:image/png;base64,' + img_str.decode()
		final_slices.append(img_str)

		upper = upper + slice_size
		count = count + 1

	return final_slices

long_slice()



