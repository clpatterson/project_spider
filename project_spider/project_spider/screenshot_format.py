import io
import base64
import math
from PIL import Image
from fpdf import FPDF
import boto
from boto.s3.key import Key


def long_slice(image_data):
	"""Takes image and chops so it can be
	displayed across multiple pages of a pdf."""

	# Process binary data and open.
	im = image_data.split('base64,')[1]
	im = base64.b64decode(im)
	im = io.BytesIO(im)
	
	img = Image.open(im)
	width, height = img.size
	upper = 0
	left = 0
	
	# Max height to fit pdf.
	max_height_mm = 198
	max_height = (max_height_mm * 96) / 25.4

	slice_size = max_height

	slices = int(math.ceil(height/slice_size))
	count = 1

	final_slices = []
	for slice in range(slices):
		# If no more slices needed, set the lower bound to bottom of image.
		if count == slices:
			lower = height
		else:
			lower = int(count * slice_size)  
		 
		# Set the bounding box.     
		bbox = (left, upper, width, lower)
		working_slice = img.crop(bbox)

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


class PDF(FPDF):
	FPDF_FONTPATH = "/home/ec2-user/venv/python36/local/lib/python3.6/dist-packages/fpdf-1.7.2-py3.6.egg/fpdf/font"
	# Overide default so img can be inserted as bit object
	def load_resource(self, reason, filename):
		if reason == "image":
			if filename.startswith("http://") or filename.startswith("https://"):
				f = io.BytesIO(urlopen(filename).read())
			elif filename.startswith("data"):
				f = filename.split('base64,')[1]
				f = base64.b64decode(f)
				f = io.BytesIO(f)
			else:
				f = open(filename, "rb")
			return f
		else:
			self.error("Unknown resource loading reason \"%s\"" % reason)

	def header(self):
		# Logo
		self.image('china_file_logo.png', 10, 8, 43)
		# Arial bold 15
		self.set_font('Arial', '', 15)
		# Line break
		# self.ln(17)
		# Set coordinates
		self.set_xy(8,20)
		# Title
		self.cell(60, 10, 'Catching Tigers and Flies', 0, 1, 'C',)
		# Line break
		self.ln(5)

	# Meta-data
	def body(self, url, site_ip, time, server, title):
    	# Arial bold 15
		self.set_font('Arial', 'B', 10)
		# Set coordinates
		self.set_x(8)
		# Add unicode font
		self.add_font('fireflysung', '','fireflysung.ttf', uni=True)
    	# Title
		self.cell(50, 10, 'Document title:', 0, 0)
		self.set_font('fireflysung', '', 10)
		self.cell(40, 10, u'{}'.format(title), 0, 1)
		# Set font back to Arial
		self.set_font('Arial', 'B', 10)
    	# Set coordinates
		self.set_x(8)
    	# Capture URL
		self.cell(50, 10, 'Capture URL:', 0, 0)
		self.cell(40, 10, url, 0, 1)
		# Set coordinates
		self.set_x(8)
		# Capture site IP
		self.cell(50, 10, 'Capture site IP:', 0, 0)
		self.cell(40, 10, site_ip, 0, 1)
		# Set coordinates
		self.set_x(8)
		# Page load timestamp
		self.cell(50, 10, 'Page loaded at:', 0, 0)
		self.cell(40, 10, time, 0, 1)
		# Set coordinates
		self.set_x(8)
		# Page capture timestamp
		self.cell(50, 10, 'Capture timestamp:', 0, 0)
		self.cell(40, 10, time, 0, 1)
		# Set coordinates
		self.set_x(8)
		# Tool
		self.cell(50, 10, 'Capture tool:', 0, 0)
		self.cell(40, 10, 'v0.9.1', 0, 1)
		# Set coordinates
		self.set_x(8)
		# Operating system
		self.cell(50, 10, 'Capture site server:', 0, 0)
		self.cell(40, 10, server, 0, 1)
		# Set coordinates
		self.set_x(8)
		# PDF length
		self.cell(50, 10, 'PDF length:', 0, 0)
		self.cell(40, 10, '{nb}', 0, 1)

	def footer(self):
		# Position at 8mm from bottom
		self.set_y(-8)
		# Arial italic 8
		self.set_font('Arial', 'I', 8)
		# Page number
		self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')



def create_pdf(image_data, url, ip_address, time, server, filename, title):
	"""Create PDF instance."""
	
	# Slice image if needed.
	image_data = long_slice(image_data)

	# Create pdf.
	pdf = PDF()
	pdf.set_auto_page_break(True, margin = 2.0)
	pdf.set_margins(2, 1)
	pdf.alias_nb_pages()
	pdf.add_page()
	pdf.body(url, ip_address, time, server, title)
	pdf.add_page()
	for image in image_data:
		pdf.image(image, w = 206, type="png")
	pdf = pdf.output(filename, 'S')

	# Setup the bucket.
	c = boto.connect_s3('AKIAISDFK264UFMI5OUQ', 'NLrGixeVsrLLim1pzZTzfbCshth2yRqsvuYj4WKN')
	b = c.get_bucket('tigersandflies', validate=False)
	k = Key(b)
	k.key = 'screenshot_pdfs/' + filename
	k.set_contents_from_string(pdf)



	# For writing pdfs to a local directory
	#pdf.output('/Users/Charlie/Desktop/programming/project_spider/project_spider/pdfs/' + filename, 'F')



