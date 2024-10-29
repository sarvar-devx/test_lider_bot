from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot
from aiogram.types import FSInputFile

from db import TestAnswer, Test, Certificate


async def sending_certificates(bot: Bot, test: Test, certificate_num: int):
    font_paths = {
        'rasa': "/usr/share/fonts/truetype/fonts-yrsa-rasa/Rasa-Medium.ttf",
        'ubuntu': "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        'bold': "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    }

    colors = {
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'cyan': (0, 139, 139),
        'dark_gray': (68, 64, 80)
    }
    test_answers = await TestAnswer.get_ordered_test_answers(test.id)
    certificate = await Certificate.get(certificate_num)
    certificate_path = certificate.image_path

    name_font_path = font_paths['rasa']
    user_rank_font_path = font_paths['ubuntu']
    name_color = colors['black']
    user_rank_font = ImageFont.truetype(user_rank_font_path, size=30)

    if 4 == certificate_num or 3 == certificate_num:
        test_code = str(test.id)
        issue_date = str(datetime.now().date())
        if 3 == certificate_num:
            name_position = (400, 445)
            user_rank_position = (465, 610)
            user_rank_color = colors['cyan']
            test_code_color = colors['cyan']
            test_code_position = (777, 560)
            issue_date_position = (980, 845)
        else:
            name_position = (400, 395)
            name_color = colors['white']
            user_rank_font_path = font_paths['bold']
            user_rank_position = (805, 508)
            user_rank_color = colors['white']
            test_code_color = colors['white']
            test_code_position = (530, 510)
            issue_date_position = (1040, 820)

        test_font = ImageFont.truetype(user_rank_font_path, size=25)
        date_font = ImageFont.truetype(name_font_path, size=40)

    elif 2 == certificate_num:
        user_rank_font_path = font_paths['rasa']
        user_rank_position = (798, 557)
        user_rank_color = (50, 50, 50)
        name_position = (400, 450)
        user_rank_font = ImageFont.truetype(user_rank_font_path, size=35)
    else:
        name_font_path = font_paths['bold']
        name_position = (300, 400)
        user_rank_position = (572, 560)
        user_rank_color = colors['dark_gray']

    for user_rank, test_answer in enumerate(test_answers, 1):
        certificate = Image.open(certificate_path)
        draw = ImageDraw.Draw(certificate)
        if certificate_num == 4 or certificate_num == 3:
            draw.text(issue_date_position, issue_date, font=date_font, fill=name_color)
            draw.text(test_code_position, test_code, font=test_font, fill=test_code_color)

        name = test_answer.user.first_name.title() + ' ' + test_answer.user.last_name.title()
        name_font = ImageFont.truetype(name_font_path, size=50)
        draw.text(user_rank_position, str(user_rank), font=user_rank_font, fill=user_rank_color)
        draw.text(name_position, name, font=name_font, fill=name_color)

        certificate.save("media/sending_certificate.png")
        await bot.send_photo(test_answer.user.id, FSInputFile("media/sending_certificate.png"))
