## Task

Write a script in Python that will extract all email addresses (e-mail) from the image.

The script should receive two parameters for input:

- `--input` - the path to the image;

- `--output` - the path to the text file in which you want to write the result.

## Script algorithm

1. Reads image by path and creates PIL Image object (we can pass the path directly to tesseract, though);
2. Tries to detect the image orientation and rotate if necessary. Saves rotated image into the output path for demo
   purposes (OSD might be a problem for `tesseract` if image does not have appropriate metadata or image is not rotated by
   90/180/270 degree);
3. Calls `tesseract` with provided configs from `config.ini` (in provided);
4. Splits output string to get a list of string, goes through them and tries to find potential emails;
5. Validates all potential emails;
6. Saves all valid emails (no duplicates) into a file;

## Why did I use pytesseract exactly?

_Short answer: because it is required for this position_

As far as I found, there are a few different OCR engines that can be utilised to find text to in images:

- pytesseract;
- easyocr;
- keras_ocr;

And a lot of [others](https://en.wikipedia.org/wiki/Comparison_of_optical_character_recognition_software)

I've watched various videos comparing these engines and it seems that `tesseract` is better suited for recognizing text
from documents (this explains why some of my input images didn't work). For some of my images `easyocr` might do
better, but it is another story.

## How to run

### Install tesseract

If you do not have it, follow
the [instructions](https://github.com/tesseract-ocr/tesseract/tree/main#installing-tesseract) to install it

### Install dependencies

Create venv

```shell
python -m venv .venv
```

Install all dependencies into your venv from requirements.txt

```shell
python -m pip install -r requirements.txt
```

### Run

Run with one image

```shell
python3 main.py --input <path/to/file> --output <path/to/file>
```

Run with all images from input folder

```shell
python3 test_main.py
```

## Additional `tesseract` configs

You can find a `config.ini` file where you can put additional tesseract configs under the `[tesseract]` section. For
possible configs look [here](https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc)

## Input data

As the input data I have found some screenshots from the Internet and did a few by my own. I have grouped them into
different folders, where you have find pics with easy-to-find emails, with blur, rotated pics, pics with non-emails,
etc. **SPOILER:** not all emails were recognised correctly, but I did my best :)

## Faced issues

1. When image is rotated, but not for 90/180/270 degree it is hard to detect rotation by `tesseract`,
   usually it fails to do so and we _assume_ that the image is not rotated and that might result into incorrect
   recognition;
2. Images with bad quality might not be recognised correctly (e.g. `j` -> `|` or `|'`);
3. Single or phrase can be splitted into different words in the OCR result, so we need to assemble them somehow;

## Want can be improved

1. **Rotation issue:** As far as I found, detecting image rotation correctly is not a trivial task when we have a
   rotation not by 90 degree.
   I have found a few possible solutions if we _assume_ that the text in the image contains all text in
   same orientation, but it uses other OCR lib there. (I did not dig too deep, but I guess with can do somthing like
   that with `tesseract`. Or not, hehe)
2. **Bad quality images:** I _guess_ we can play with image itself by doing some pre-processing stuff, like changing
   contrast, etc to help OCR somehow
3. **Split**: Regarding my particular script, `find_potential_emails` func can do much better here to try to assemble
   email from next words in list; 
