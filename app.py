import os
import subprocess
import sys
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

import os
import subprocess
import sys
import json
import time
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/intro')
def intro():
    return render_template('intro.html')

@app.route('/api/info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL을 입력해주세요.'}), 400

    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            seen_res = set()
            # Filter and sort formats
            available_formats = info.get('formats', [])
            
            for f in available_formats:
                # We want video files that have height (resolution)
                if f.get('vcodec') != 'none': 
                    res = f.get('height')
                    if res and res not in seen_res:
                        formats.append({
                            'format_id': f['format_id'],
                            'resolution': f'{res}p',
                            'ext': f['ext'],
                            'filesize': f.get('filesize'),
                            'height': res
                        })
                        seen_res.add(res)
            
            # Sort by resolution high to low
            formats.sort(key=lambda x: x['height'], reverse=True)

            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string'),
                'uploader': info.get('uploader'),
                'formats': formats, # Return all formats
                'original_url': url
            })
    except Exception as e:
        return jsonify({'error': f'분석 실패: {str(e)}'}), 500

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    type = data.get('type', 'video') # video or audio
    format_id = data.get('format_id') # Optional for specific video quality
    
    if not url:
        return jsonify({'error': 'URL이 필요합니다.'}), 400

    @stream_with_context
    def generate():
        try:
            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        p = d.get('_percent_str', '0%').replace('%','')
                        speed = d.get('_speed_str', 'N/A')
                        yield json.dumps({'status': 'downloading', 'percent': p, 'speed': speed, 'message': f'{p}% 완료 ({speed})'}) + '\n'
                    except:
                        pass
                elif d['status'] == 'finished':
                    yield json.dumps({'status': 'processing', 'percent': '100', 'message': '변환 및 저장 중...'}) + '\n'

            ydl_opts = {
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'quiet': True,
                'progress_hooks': [progress_hook],
                'noplaylist': True,
            }
            
            if type == 'audio':
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            else:
                # If a specific format is requested + best audio, otherwise best
                if format_id:
                     ydl_opts.update({
                        'format': f'{format_id}+bestaudio/best',
                        'merge_output_format': 'mp4' 
                    })
                else:
                    ydl_opts.update({
                        'format': 'bestvideo+bestaudio/best',
                        'merge_output_format': 'mp4'
                    })

            yield json.dumps({'status': 'start', 'message': '다운로드 시작...'}) + '\n'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if type == 'audio':
                    filename = os.path.splitext(filename)[0] + '.mp3'
                
                final_name = os.path.basename(filename)
                yield json.dumps({'status': 'complete', 'message': '다운로드 완료!', 'filename': final_name}) + '\n'

        except Exception as e:
            yield json.dumps({'status': 'error', 'message': f'에러 발생: {str(e)}'}) + '\n'

    return Response(generate(), mimetype='application/json')

@app.route('/api/open_folder', methods=['POST'])
def open_folder():
    path = DOWNLOAD_FOLDER
    if sys.platform == 'linux':
        subprocess.call(['xdg-open', path])
    elif sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.call(['open', path])
    return jsonify({'success': True})

@app.route('/api/open_file', methods=['POST'])
def open_file():
    data = request.json
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': '파일명이 필요합니다.'}), 400
        
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404

    if sys.platform == 'linux':
        subprocess.call(['xdg-open', filepath])
    elif sys.platform == 'win32':
        os.startfile(filepath)
    elif sys.platform == 'darwin':
        subprocess.call(['open', filepath])
        
    return jsonify({'success': True})

if __name__ == '__main__':
    print(f"Starting server... Open http://localhost:5000 in your browser.")
    app.run(debug=True, port=5000)
