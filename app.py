import os
import uuid
from flask import Flask, render_template, request, send_file, session, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, ImageEnhance
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64

from captcha import generate_captcha, verify_captcha
from nn_model import predict_image_category
from utils import create_histogram, allowed_file
from config import config

# Создаем приложение
app = Flask(__name__)

# Загружаем конфигурацию
env = os.environ.get('FLASK_ENV', 'default')
app.config.from_object(config[env])
config[env].init_app(app)  # Инициализируем приложение

# Добавляем секретный ключ из переменных окружения
app.secret_key = app.config['SECRET_KEY']

# ... остальной код остается таким же ...
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GRAPH_FOLDER'] = 'static/graphs'

# Создаем папки если их нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GRAPH_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    # Генерируем новую капчу при заходе на главную
    captcha_text, captcha_image = generate_captcha()
    session['captcha_text'] = captcha_text
    
    # Конвертируем изображение в base64 для HTML
    buffered = BytesIO()
    captcha_image.save(buffered, format="PNG")
    captcha_b64 = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template('index.html', 
                          captcha_image=captcha_b64,
                          max_contrast=3.0,  # Максимальное значение контраста
                          min_contrast=0.1)  # Минимальное значение

@app.route('/process', methods=['POST'])
def process_image():
    try:
        # Проверяем капчу
        user_captcha = request.form.get('captcha', '').strip()
        if not verify_captcha(user_captcha, session.get('captcha_text')):
            return jsonify({'error': 'Неверная капча'}), 400
        
        # Проверяем файл
        if 'image' not in request.files:
            return jsonify({'error': 'Нет файла изображения'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Неподдерживаемый формат файла'}), 400
        
        # Получаем уровень контраста
        try:
            contrast_level = float(request.form.get('contrast', 1.0))
            contrast_level = max(0.1, min(3.0, contrast_level))  # Ограничиваем диапазон
        except:
            contrast_level = 1.0
        
        # Сохраняем оригинальное изображение
        original_filename = secure_filename(file.filename)
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                    f"original_{uuid.uuid4()}_{original_filename}")
        file.save(original_path)
        
        # Обрабатываем изображение
        with Image.open(original_path) as img:
            # Конвертируем в RGB если нужно
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Изменяем контраст
            enhancer = ImageEnhance.Contrast(img)
            enhanced_img = enhancer.enhance(contrast_level)
            
            # Сохраняем результат
            result_filename = f"result_{uuid.uuid4()}.png"
            result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
            enhanced_img.save(result_path)
            
            # Создаем гистограммы
            original_hist = create_histogram(img, 'original')
            enhanced_hist = create_histogram(enhanced_img, 'enhanced')
            
            # Получаем классификацию от нейросети
            category = predict_image_category(enhanced_img)
            
            # Конвертируем изображения в base64 для отображения
            buffered_original = BytesIO()
            img.save(buffered_original, format="PNG")
            original_b64 = base64.b64encode(buffered_original.getvalue()).decode()
            
            buffered_result = BytesIO()
            enhanced_img.save(buffered_result, format="PNG")
            result_b64 = base64.b64encode(buffered_result.getvalue()).decode()
            
            return jsonify({
                'success': True,
                'original_image': original_b64,
                'result_image': result_b64,
                'original_histogram': original_hist,
                'enhanced_histogram': enhanced_hist,
                'contrast_level': contrast_level,
                'category': category,
                'result_filename': result_filename
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_image(filename):
    return send_file(
        os.path.join(app.config['UPLOAD_FOLDER'], filename),
        as_attachment=True,
        download_name=f"contrast_adjusted_{filename}"
    )

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
