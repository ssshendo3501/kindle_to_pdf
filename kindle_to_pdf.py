#!/usr/bin/env python3
"""
Kindle本をPDF化するツール
Kindle for Macアプリのスクリーンショットを自動で撮影し、PDFに結合する
"""

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def get_kindle_window_id():
    """KindleアプリのウィンドウID（CGWindowID）を取得"""
    try:
        import Quartz
    except ImportError:
        print("エラー: PyObjCがインストールされていません。")
        print("インストール: pip install pyobjc-framework-Quartz")
        sys.exit(1)

    # ウィンドウ一覧を取得
    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID
    )

    kindle_windows = []
    for window in window_list:
        owner_name = window.get('kCGWindowOwnerName', '')

        # Kindleアプリのウィンドウを探す
        if owner_name == 'Kindle':
            window_id = window.get('kCGWindowNumber')
            bounds = window.get('kCGWindowBounds', {})
            width = bounds.get('Width', 0)
            height = bounds.get('Height', 0)
            # サイズが十分なウィンドウのみ（メインウィンドウ）
            if width > 100 and height > 100:
                kindle_windows.append((window_id, width * height))

    if kindle_windows:
        # 最も大きいウィンドウを選択
        kindle_windows.sort(key=lambda x: x[1], reverse=True)
        return str(kindle_windows[0][0])

    print("エラー: Kindleウィンドウが見つかりません。Kindleアプリを起動して本を開いてください。")
    sys.exit(1)


def activate_kindle():
    """Kindleアプリをアクティブ化"""
    script = '''
    tell application "Amazon Kindle"
        activate
    end tell
    '''
    subprocess.run(['osascript', '-e', script], check=True)
    time.sleep(0.5)


def capture_window(window_id, filepath):
    """指定ウィンドウのスクリーンショットを撮影（PyObjC使用）"""
    import Quartz
    from Quartz import CGWindowListCreateImage, CGRectNull, kCGWindowListOptionIncludingWindow, kCGWindowImageDefault

    # ウィンドウをキャプチャ
    image = CGWindowListCreateImage(
        CGRectNull,
        kCGWindowListOptionIncludingWindow,
        int(window_id),
        kCGWindowImageDefault
    )

    if image is None:
        raise RuntimeError(f"ウィンドウ {window_id} のキャプチャに失敗しました")

    # PNGとして保存
    from Quartz import CGImageDestinationCreateWithURL, CGImageDestinationAddImage, CGImageDestinationFinalize
    from Foundation import NSURL

    url = NSURL.fileURLWithPath_(filepath)
    dest = CGImageDestinationCreateWithURL(url, 'public.png', 1, None)
    CGImageDestinationAddImage(dest, image, None)
    CGImageDestinationFinalize(dest)


def send_page_turn():
    """Kindleで次のページへ移動（右矢印キー）"""
    script = '''
    tell application "System Events"
        tell process "Kindle"
            key code 124
        end tell
    end tell
    '''
    subprocess.run(['osascript', '-e', script], check=True)


def get_image_hash(filepath):
    """画像ファイルのハッシュ値を取得"""
    from PIL import Image
    import hashlib

    with Image.open(filepath) as img:
        return hashlib.md5(img.tobytes()).hexdigest()


def images_to_pdf(image_dir, output_path):
    """画像ファイルをPDFに結合（Pillowを使用）"""
    try:
        from PIL import Image
    except ImportError:
        print("エラー: Pillowがインストールされていません。")
        print("インストール: pip install Pillow")
        sys.exit(1)

    image_files = sorted(Path(image_dir).glob("page_*.png"))

    if not image_files:
        print("エラー: 画像ファイルが見つかりません。")
        sys.exit(1)

    print(f"\n{len(image_files)}枚の画像をPDFに結合中...")

    # 最初の画像を開く
    images = []
    for img_path in image_files:
        img = Image.open(img_path)
        # RGBAをRGBに変換（PNGの透過対応）
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            images.append(rgb_img)
        else:
            images.append(img.convert('RGB'))

    # PDFとして保存
    if images:
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            resolution=100.0
        )

    print(f"PDF作成完了: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Kindle本をPDF化するツール"
    )
    parser.add_argument(
        "--pages", "-p",
        type=int,
        default=None,
        help="キャプチャするページ数（省略時は自動検出）"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="出力PDFファイル名"
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=1.0,
        help="ページ送り後の待機秒数（デフォルト: 1.0）"
    )
    parser.add_argument(
        "--start-page", "-s",
        type=int,
        default=1,
        help="開始ページ番号（途中再開用、デフォルト: 1）"
    )
    parser.add_argument(
        "--keep-images", "-k",
        action="store_true",
        help="終了後も画像を保持する"
    )

    args = parser.parse_args()

    # 出力ファイル名の処理
    output_path = args.output
    if not output_path.endswith(".pdf"):
        output_path += ".pdf"

    # 一時ディレクトリの作成
    if args.keep_images:
        image_dir = Path("kindle_screenshots")
        image_dir.mkdir(exist_ok=True)
    else:
        temp_dir = tempfile.mkdtemp(prefix="kindle_pdf_")
        image_dir = Path(temp_dir)

    auto_detect = args.pages is None

    print("=" * 50)
    print("Kindle PDF化ツール")
    print("=" * 50)
    print(f"ページ数: {'自動検出' if auto_detect else args.pages}")
    print(f"出力ファイル: {output_path}")
    print(f"待機時間: {args.delay}秒")
    print(f"画像保存先: {image_dir}")
    print("=" * 50)

    # Kindleをアクティブ化
    print("\nKindleアプリをアクティブ化中...")
    activate_kindle()

    # ウィンドウIDを取得
    print("KindleウィンドウIDを取得中...")
    window_id = get_kindle_window_id()
    print(f"ウィンドウID: {window_id}")

    # 開始前の確認
    print("\n" + "=" * 50)
    print("準備完了！")
    print("Kindleアプリで最初のページを表示していることを確認してください。")
    print("3秒後にキャプチャを開始します...")
    print("=" * 50)
    time.sleep(3)

    # キャプチャループ
    try:
        page_num = args.start_page
        last_hash = None
        same_count = 0
        max_pages = args.pages if args.pages else 99999

        while page_num <= max_pages:
            filepath = image_dir / f"page_{page_num:04d}.png"

            # スクリーンショット撮影
            capture_window(window_id, str(filepath))

            # 自動検出モード: 同じ画像が3回続いたら終了
            if auto_detect:
                current_hash = get_image_hash(str(filepath))
                if current_hash == last_hash:
                    same_count += 1
                    if same_count >= 3:
                        # 重複した画像を削除
                        for i in range(same_count):
                            dup_path = image_dir / f"page_{page_num - i:04d}.png"
                            if dup_path.exists():
                                dup_path.unlink()
                        page_num -= same_count
                        print(f"\r最後のページを検出しました（{page_num}ページ）")
                        break
                else:
                    same_count = 0
                last_hash = current_hash

            # 進捗表示
            if auto_detect:
                print(f"\rページ {page_num} をキャプチャ中...", end="", flush=True)
            else:
                progress = (page_num / args.pages) * 100
                print(f"\rページ {page_num}/{args.pages} ({progress:.1f}%)", end="", flush=True)

            # ページ送り
            send_page_turn()
            time.sleep(args.delay)
            page_num += 1

    except KeyboardInterrupt:
        print("\n\n中断されました。")
        print(f"画像は {image_dir} に保存されています。")
        print(f"再開するには: --start-page {page_num} を指定してください。")
        sys.exit(1)

    print("\n\nキャプチャ完了！")

    # PDFに結合
    images_to_pdf(image_dir, output_path)

    # 一時ファイルの削除
    if not args.keep_images:
        import shutil
        shutil.rmtree(image_dir)
        print("一時ファイルを削除しました。")
    else:
        print(f"画像は {image_dir} に保存されています。")

    print("\n完了！")


if __name__ == "__main__":
    main()
