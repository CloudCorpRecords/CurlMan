URL: https://ai.google.dev/gemini-api/docs/document-processing?lang=python
---
[![Gemini API](https://ai.google.dev/_static/googledevai/images/lockup-new.svg)](/)

`/`

- English
- Deutsch
- Español – América Latina
- Français
- Indonesia
- Italiano
- Polski
- Português – Brasil
- Shqip
- Tiếng Việt
- Türkçe
- Русский
- עברית
- العربيّة
- فارسی
- हिंदी
- বাংলা
- ภาษาไทย
- 中文 – 简体
- 中文 – 繁體
- 日本語
- 한국어

Sign in

Gemini 2.0 Flash Experimental is now available! [Learn more](https://developers.googleblog.com/en/the-next-chapter-of-the-gemini-era-for-developers/)

- [Home](https://ai.google.dev/)
- [Gemini API](https://ai.google.dev/gemini-api)
- [Models](https://ai.google.dev/gemini-api/docs)



 Send feedback



# Explore document processing capabilities with the Gemini API

PythonNode.jsGoREST

The Gemini API can process and run inference on PDF documents passed to it. When
a PDF is uploaded, the Gemini API can:

- Describe or answer questions about the content
- Summarize the content
- Extrapolate from the content

This tutorial demonstrates some possible ways to prompt the Gemini API with
provided PDF documents. All output is text-only.

## Before you begin: Set up your project and API key

Before calling the Gemini API, you need to set up your project and configure
your API key.

**Expand to view how to set up your project and API key**

### Get and secure your API key

You need an API key to call the Gemini API. If you don't already have one,
create a key in Google AI Studio.

[Get an API key](https://aistudio.google.com/app/apikey)

It's strongly recommended that you do _not_ check an API key into your version
control system.

You should store your API key in a secrets store such as Google Cloud
[Secret Manager](https://cloud.google.com/secret-manager/docs).

This tutorial assumes that you're accessing your API key as an environment
variable.

### Install the SDK package and configure your API key

The Python SDK for the Gemini API is contained in the
[`google-generativeai`](https://pypi.org/project/google-generativeai/) package.

1. Install the dependency using pip:




```
pip install -U google-generativeai

```

2. Import the package and configure the service with your API key:




```
import os
import google.generativeai as genai

genai.configure(api_key=os.environ['API_KEY'])

```


## Technical details

Gemini 1.5 Pro and 1.5 Flash support a maximum of 3,600 document pages. Document
pages must be in one of the following text data MIME types:

- PDF - `application/pdf`
- JavaScript - `application/x-javascript`, `text/javascript`
- Python - `application/x-python`, `text/x-python`
- TXT - `text/plain`
- HTML - `text/html`
- CSS - `text/css`
- Markdown - `text/md`
- CSV - `text/csv`
- XML - `text/xml`
- RTF - `text/rtf`

Each document page is equivalent to 258 tokens.

While there are no specific limits to the number of pixels in a document besides
the model's context window, larger pages are scaled down to a maximum resolution
of 3072x3072 while preserving their original aspect ratio, while smaller pages
are scaled up to 768x768 pixels. There is no cost reduction for pages at lower
sizes, other than bandwidth, or performance improvement for pages at higher
resolution.

For best results:

- Rotate pages to the correct orientation before uploading.
- Avoid blurry pages.
- If using a single page, place the text prompt after the page.

## Upload a document and generate content

You can use the File API to upload a document of any size. Always use the File
API when the total request size (including the files, text prompt, system
instructions, etc.) is larger than 20 MB.

Call [`media.upload`](/api/rest/v1beta/media/upload) to upload a file using the
File API. The following code uploads a document file and then uses the file in a
call to
[`models.generateContent`](/api/generate-content#method:-models.generatecontent).

```
import google.generativeai as genai

model = genai.GenerativeModel("gemini-1.5-flash")
sample_pdf = genai.upload_file(media / "test.pdf")
response = model.generate_content(["Give me a summary of this pdf file.", sample_pdf])
print(response.text)
files.py

```

## Get metadata for a file

You can verify the API successfully stored the uploaded file and get its
metadata by calling [`files.get`](/api/rest/v1beta/files/get). Only the `name`
(and by extension, the `uri`) are unique.

```
import google.generativeai as genai

myfile = genai.upload_file(media / "poem.txt")
file_name = myfile.name
print(file_name)  # "files/*"

myfile = genai.get_file(file_name)
print(myfile)
files.py

```

## Upload one or more locally stored files

Alternatively, you can upload one or more locally stored files.

When the combination of files and system instructions that you intend to send is
larger than 20MB in size, use the File API to upload those files, as previously
shown. Smaller files can instead be called locally from the Gemini API:

```
import PyPDF2

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text
        return extracted_text

sample_file_2 = extract_text_from_pdf('example-1.pdf')
sample_file_3 = extract_text_from_pdf('example-2.pdf')

```

## Prompt with multiple documents

You can provide the Gemini API with any combination of documents and text that
fit within the model's context window. This example provides one short text
prompt and three documents previously uploaded:

```
# Choose a Gemini model.
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

prompt = "Summarize the differences between the thesis statements for these documents."

response = model.generate_content([prompt, sample_file, sample_file_2, sample_file_3])

print(response.text)

```

## List files

You can list all files uploaded using the File API and their URIs using
[`files.list`](/api/files#method:-files.list).

```
import google.generativeai as genai

print("My files:")
for f in genai.list_files():
    print("  ", f.name)
files.py

```

## Delete files

Files uploaded using the File API are automatically deleted after 2 days. You
can also manually delete them using
[`files.delete`](/api/files#method:-files.delete).

```
import google.generativeai as genai

myfile = genai.upload_file(media / "poem.txt")

myfile.delete()

try:
    # Error.
    model = genai.GenerativeModel("gemini-1.5-flash")
    result = model.generate_content([myfile, "Describe this file."])
except google.api_core.exceptions.PermissionDenied:
    pass
files.py

```

## What's next

This guide shows how to use
[`generateContent`](/api/generate-content#method:-models.generatecontent) and
to generate text outputs from processed documents. To learn more,
see the following resources:

- [File prompting strategies](/gemini-api/docs/file-prompting-strategies): The
Gemini API supports prompting with text, image, audio, and video data, also
known as multimodal prompting.
- [System instructions](/gemini-api/docs/system-instructions): System
instructions let you steer the behavior of the model based on your specific
needs and use cases.
- [Safety guidance](/gemini-api/docs/safety-guidance): Sometimes generative AI
models produce unexpected outputs, such as outputs that are inaccurate,
biased, or offensive. Post-processing and human evaluation are essential to
limit the risk of harm from such outputs.



 Send feedback



Except as otherwise noted, the content of this page is licensed under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/), and code samples are licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0). For details, see the [Google Developers Site Policies](https://developers.google.com/site-policies). Java is a registered trademark of Oracle and/or its affiliates.

Last updated 2024-12-11 UTC.


Need to tell us more?


\[\[\["Easy to understand","easyToUnderstand","thumb-up"\],\["Solved my problem","solvedMyProblem","thumb-up"\],\["Other","otherUp","thumb-up"\]\],\[\["Missing the information I need","missingTheInformationINeed","thumb-down"\],\["Too complicated / too many steps","tooComplicatedTooManySteps","thumb-down"\],\["Out of date","outOfDate","thumb-down"\],\["Samples / code issue","samplesCodeIssue","thumb-down"\],\["Other","otherDown","thumb-down"\]\],\["Last updated 2024-12-11 UTC."\],\[\],\[\]\]