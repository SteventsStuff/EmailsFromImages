# Тестове завдання:
# Написати скрипт на Python, який буде витягувати всі електронні адреси (e-mail) із зображення.
# Скрипт повинен отримувати на вхід два параметри:
# --input - шлях к зображенню
# --output - шлях до текстового файлу, в який потрібно записати результат.

import os
import sys
import string
import argparse
import configparser

import pytesseract
from pytesseract import Output
from PIL import Image
from email_validator import validate_email, EmailNotValidError

RECOGNITION_TIMEOUT: float = 60.0
POSSIBLE_ROTATION_THRESHOLD: float = 5.0
#
CHARS_TO_STRIP: str = string.punctuation.replace('@', '').replace('.', '')  # !"#$%&\'()*+,-/:;<=>?[\\]^_`{|}~


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='EmailFromImageParser', description='Gets emails from an image')

    parser.add_argument('--input', dest='input', help='Path to an image')
    parser.add_argument('--output', dest='output', help='Path to a result text file')

    return parser


def get_tesseract_config() -> str:
    tesseract_configs = ''

    config_parser = configparser.ConfigParser()
    configs = config_parser.read('config.ini')
    if not configs:
        return tesseract_configs

    tesseract_configs = ' '.join([f'--{k} {v}' for k, v in config_parser.items('tesseract')])
    print(f'Found next tesseract configs: {tesseract_configs}; They will be applied to all tesseract commands')
    return tesseract_configs


def read_image(filepath: str | None) -> Image:
    try:
        return Image.open(filepath)
    except (TypeError, FileNotFoundError) as e:
        raise ValueError(
            f'Failed to read file: {filepath}. Make sure you passed a valid file path. Error: {e}'
        ) from e


def write_emails_to_file(filepath: str, emails: list[str]) -> None:
    if os.path.exists(filepath):
        print(f'NOTE: {filepath} already exists. It will be overwritten!')

    print(f'Saving result to {filepath}')
    with open(filepath, 'w') as f:
        f.write('\n'.join(emails))


def normalize_image_orientation(image: Image, tesseract_config: str) -> tuple[Image, bool]:
    is_rotated = False

    try:
        osd_result = pytesseract.image_to_osd(image, output_type=Output.DICT, config=tesseract_config)
    except pytesseract.pytesseract.TesseractError as e:
        # NOTE: for 'cat' case
        print(f'Failed to determine the image orientation. Assuming that image is not rotated. Error: {e}')
        return image, is_rotated
    print(f'OSD: {osd_result}')

    try:
        angle_rotated_image = osd_result['rotate']
    except (TypeError, KeyError) as e:
        print(f'Failed to find rotate value. Assuming that image is not rotated. Error: {e}')
        return image, is_rotated

    # NOTE: assuming that unless image is rotated less than 5 degree it is fine to find text
    # NOTE: ignoring "Orientation confidence"
    if abs(angle_rotated_image) > POSSIBLE_ROTATION_THRESHOLD:
        print(f'Rotate value if more then {POSSIBLE_ROTATION_THRESHOLD}. Rotating image...')
        rotate_angle = -1 * angle_rotated_image
        image = image.rotate(rotate_angle, expand=True)
        is_rotated = True

    return image, is_rotated


def get_emails_from_image(image: Image, tesseract_config: str) -> list[str]:
    emails = set()

    try:
        text_from_image = pytesseract.image_to_string(image, timeout=RECOGNITION_TIMEOUT, config=tesseract_config)
    except RuntimeError as e:
        print(f'Failed to recognise text. Try to extend a timeout threshold. Error: {e}')
        return list(emails)

    potential_emails = find_potential_emails(text_from_image)
    for potential_email in potential_emails:
        try:
            # check_deliverability=False to disable DNS check (hence not handling EmailUndeliverableError)
            validated_email = validate_email(potential_email, check_deliverability=False)
        except EmailNotValidError as e:
            print(f'{potential_email} is invalid. Error: {e}')
            continue
        else:
            emails.add(validated_email.normalized)

    print(f'Found {len(emails)} email(s) (no duplicates)')
    return list(emails)


def find_potential_emails(text: str) -> list[str]:
    """
    We could just do `potential_emails = [s.strip(CHARS_TO_STRIP) for s in normalised_text if '@' in s]`
    on a list with string, but it won't cover edge cases like ["foo", "@bar.com"] where we have a valid foo@bar.com
    email address, etc.
    It is still not the best possible solution, though, since it does not cover cases like:
    ["blah", "haha", "@", "lorem", "foo", "@", "bar", ".", "com", "txt"] where we have foo@bar.com
    """
    normalised_text = ' '.join(text.split('\n')).split()

    potential_emails = []
    for index, word in enumerate(normalised_text):
        potential_email = ''
        if '@' not in word:
            # check next word if it has @
            if index >= len(normalised_text) - 1:
                continue

            next_word = normalised_text[index + 1]
            if not next_word.startswith('@'):
                continue

            at_index = next_word.find('@')  # NOTE: "@" is called "at"
            dot_index = next_word.find('.')
            # NOTE: @ must be before "." and "@." not valid
            if at_index > dot_index or dot_index - 1 == at_index:
                continue

            potential_email = word + next_word

        elif word.endswith('@'):
            if index >= len(normalised_text) - 1:
                continue
            potential_email = word + normalised_text[index + 1]

        elif '@' in word and not word.startswith('@'):
            potential_email = word

        if potential_email:
            # NOTE: stripping by '!"#$%&\'()*+,-./:;<=>?[\\]^_`{|}~' to handler cases like: <foo@example.com>,
            # or [foo@example.com], etc
            potential_emails.append(potential_email.strip(CHARS_TO_STRIP))

    print(f'Strings with potential emails: {potential_emails}')
    return potential_emails


def save_rotated_image(image: Image, parsed_args: argparse.Namespace) -> None:
    original_filename, extension = parsed_args.input.split('/')[-1].split('.')
    output_dir_path = '/'.join(parsed_args.output.split('/')[:-1])
    rotated_path = f'{output_dir_path}/{original_filename}-rotated.{extension}'
    print(f'Saving rotated image in: {rotated_path}')
    image.save(rotated_path)


def main(args: list[str]) -> None:
    parsed_args = get_arg_parser().parse_args(args)

    tesseract_config = get_tesseract_config()

    image = read_image(parsed_args.input)
    normalized_image, is_rotated = normalize_image_orientation(image, tesseract_config)
    if is_rotated:
        # NOTE: optional step really, did it just for demo and debugging purposes
        save_rotated_image(normalized_image, parsed_args)

    emails = get_emails_from_image(normalized_image, tesseract_config)
    if not emails:
        print('No emails found. Make sure you did not pass an image with a cat or somthing...')
        return

    write_emails_to_file(parsed_args.output, emails)


if __name__ == '__main__':
    # slicing to ignore the script name
    main(sys.argv[1:])
