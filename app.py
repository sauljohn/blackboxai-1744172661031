from flask import Flask, render_template, request, jsonify, send_file
from pytube import YouTube
import instaloader
import os
import tempfile
from tqdm import tqdm

app = Flask(__name__)

# Initialize Instaloader
L = instaloader.Instaloader()

def download_youtube_video(url, quality='highest'):
    try:
        yt = YouTube(url)
        if quality == 'highest':
            stream = yt.streams.get_highest_resolution()
        else:
            stream = yt.streams.get_by_resolution(quality)
        
        temp_dir = tempfile.mkdtemp()
        file_path = stream.download(output_path=temp_dir)
        return file_path
    except Exception as e:
        raise Exception(f"YouTube download error: {str(e)}")

def download_instagram_video(url):
    try:
        shortcode = url.split('/')[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, f"instagram_{shortcode}.mp4")
        
        with tqdm(total=1, desc="Downloading") as pbar:
            L.download_post(post, target=temp_dir)
            pbar.update(1)
        
        # Find the downloaded video file
        for file in os.listdir(temp_dir):
            if file.endswith('.mp4'):
                return os.path.join(temp_dir, file)
        raise Exception("No video file found")
    except Exception as e:
        raise Exception(f"Instagram download error: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_video_info', methods=['POST'])
def get_video_info():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        if 'youtube.com' in url or 'youtu.be' in url:
            yt = YouTube(url)
            return jsonify({
                'platform': 'youtube',
                'title': yt.title,
                'thumbnail': yt.thumbnail_url,
                'qualities': [stream.resolution for stream in yt.streams.filter(progressive=True)]
            })
        elif 'instagram.com' in url:
            shortcode = url.split('/')[-2]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            return jsonify({
                'platform': 'instagram',
                'thumbnail': post.url,
                'qualities': ['standard']
            })
        else:
            return jsonify({'error': 'Unsupported platform'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    quality = data.get('quality', 'highest')
    
    try:
        if 'youtube.com' in url or 'youtu.be' in url:
            file_path = download_youtube_video(url, quality)
        elif 'instagram.com' in url:
            file_path = download_instagram_video(url)
        else:
            return jsonify({'error': 'Unsupported platform'}), 400
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
