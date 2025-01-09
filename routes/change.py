from flask import Flask, render_template, request, redirect, url_for, send_file, session, Blueprint
import os
from routes.negaposi import negaposi
from routes.mosaic import MosaicCov
from routes.Gaussian import gaussian
from routes.Thresholding import thresholding
from routes.edge_detection import edge_detection
from routes.img_quality import enhance_image_advanced
from routes.Inversion import inversion
from models import History, User
import base64
import datetime

# Blueprintの作成
change_bp = Blueprint('change', __name__, url_prefix='/change')

#ボタンを押して画像をstatic内に保存されるようにする-----------------------------------------------------------------------------------------------
@change_bp.route('/upload', methods=['POST'])
def upload():
    # ファイルがアップロードされたか確認(本当はアラートを出したいがjsを使わなければならないので、時間が余ったら実装する)
    if 'file' not in request.files:
        return 'ファイルが選択されていません。', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'ファイルが選択されていません。', 400
    
    if file:
        filepath = os.path.join('static', 'img.png')
        file.save(filepath)
        return redirect(url_for('change.change', user_name = session['user_name']))


#change.htmlのエンドポイント------------------------------------------------------------------------------------------------------
@change_bp.route('/<user_name>')
def change(user_name):
    #Historyデータの抽出
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    histories = History.select().where(History.user == user)
    return render_template('change.html', histories = histories, user_name = user_name)


#画像変換ようのエンドポイント------------------------------------------------------------------------------------------------------
@change_bp.route('/conv',  methods=['POST'])
def conv():
    #変換用モジュールのインスタンス化
    nega = negaposi()
    mosic = MosaicCov()
    input_file_name = "static/img.png"
    output_file_name = "static/output.png"
    # `select` タグで選択された値を取得
    selected_value = request.form.get('selected_option')
    if selected_value=="":
        return '変換方法を選択してください', 400
    elif selected_value == "1":
        nega.negaposi_ms()
        conv_message = "画像の画像内の濃淡を入れ替える変換です。画像内の明るい画素を暗い画素に、暗い画素を明るい画素に変換する処理です。"
    elif selected_value == "2":
        # モザイク処理の強度取得
        mosaic_strength = request.form.get('mosaic_strength', type=int)
        if mosaic_strength is None or mosaic_strength < 1:
            return "モザイクの強度は1以上にしてください。", 400
        mosic.load_image()
        mosic.set_strength(mosaic_strength)
        mosic_img = mosic.mosaic()
        mosic.save_image(mosic_img)
        conv_message = "アップロードした画像にモザイク処理を施す"
    elif selected_value == "3":
        gaussian()
        conv_message = "アップロードした画像にガウシアンフィルタを施す"
    elif selected_value == "4":
        thresholding(input_file_name, output_file_name)
        conv_message = "アップロードした画像に二値化処理を施す"
    elif selected_value == "5":
        edge_detection(input_file_name, output_file_name)
        conv_message = "アップロードした画像にエッジ処理を施す"
    elif selected_value == "6":
        enhance_image_advanced(input_file_name)
        conv_message = "アップロードされた画像に色彩処理を施す"
    elif selected_value == "7":
        inversion()
        conv_message = "アップロードした画像に左右反転を施す"

    #change.html内で変換された画像とメッセージが表示されるようにする
    output_path = os.path.join('static', 'output.png')
    file_exists = os.path.exists(output_path)

    #bace64を用いて画像データをエンコードする
    with open(output_path, "rb") as output_file:
        encord_img_data = base64.b64encode(output_file.read())

    # 現在のログインユーザーを取得
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    print(f"user={user}")

    #Historyデータベースにエンコードした画像データと変換日時を代入する
    History.create(
        user = user,
        times = datetime.datetime.now(),
        image_data = encord_img_data
    )

    #Historyデータの抽出
    #histories = History.select()
    histories = History.select().where(History.user == user)
    print(f"his={histories}")
    return render_template('change.html', 
                           file_exists=file_exists, 
                           message=conv_message, 
                           histories = histories, 
                           user_name = session['user_name'])


#変換画像ダウンロードようのエンドポイント------------------------------------------------------------------------------------------------------
@change_bp.route('/download', methods=['POST'])
def download():
    output_path = os.path.join('static', 'output.png')
    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=True, download_name='output.png')
    else:
        return "変換された画像が見つかりません。", 404

