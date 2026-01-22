#!/usr/bin/env python3
"""
Kindle本をPDF化するツール（GUI版）
tkinterを使用したGUIアプリケーション
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class KindleToPdfApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kindle to PDF")
        self.root.resizable(False, False)

        # 状態管理
        self.is_running = False
        self.should_cancel = False
        self.capture_thread = None

        self._setup_ui()
        self._center_window()

    def _center_window(self):
        """ウィンドウを画面中央に配置"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _setup_ui(self):
        """UIコンポーネントの設定"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # 出力ファイル
        ttk.Label(main_frame, text="出力ファイル:").grid(row=0, column=0, sticky="w", pady=(0, 5))

        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        file_frame.columnconfigure(0, weight=1)

        self.output_var = tk.StringVar()
        self.output_entry = ttk.Entry(file_frame, textvariable=self.output_var, width=40)
        self.output_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.browse_btn = ttk.Button(file_frame, text="参照...", command=self._browse_output)
        self.browse_btn.grid(row=0, column=1)

        # ページ数設定
        ttk.Label(main_frame, text="ページ数:").grid(row=2, column=0, sticky="w", pady=(0, 5))

        page_frame = ttk.Frame(main_frame)
        page_frame.grid(row=3, column=0, sticky="w", pady=(0, 15))

        self.page_mode = tk.StringVar(value="auto")

        auto_radio = ttk.Radiobutton(
            page_frame, text="自動検出（推奨）",
            variable=self.page_mode, value="auto",
            command=self._on_page_mode_change
        )
        auto_radio.grid(row=0, column=0, sticky="w")

        manual_frame = ttk.Frame(page_frame)
        manual_frame.grid(row=1, column=0, sticky="w", pady=(5, 0))

        manual_radio = ttk.Radiobutton(
            manual_frame, text="指定:",
            variable=self.page_mode, value="manual",
            command=self._on_page_mode_change
        )
        manual_radio.grid(row=0, column=0)

        self.page_count_var = tk.StringVar(value="100")
        self.page_count_entry = ttk.Entry(manual_frame, textvariable=self.page_count_var, width=8, state="disabled")
        self.page_count_entry.grid(row=0, column=1, padx=(5, 5))

        ttk.Label(manual_frame, text="ページ").grid(row=0, column=2)

        # 待機時間
        delay_frame = ttk.Frame(main_frame)
        delay_frame.grid(row=4, column=0, sticky="w", pady=(0, 20))

        ttk.Label(delay_frame, text="待機時間:").grid(row=0, column=0)

        self.delay_var = tk.StringVar(value="1.0")
        delay_entry = ttk.Entry(delay_frame, textvariable=self.delay_var, width=6)
        delay_entry.grid(row=0, column=1, padx=(10, 5))

        ttk.Label(delay_frame, text="秒").grid(row=0, column=2)

        # 開始/キャンセルボタン
        self.start_btn = ttk.Button(
            main_frame, text="PDF作成開始",
            command=self._start_capture,
            style="Accent.TButton"
        )
        self.start_btn.grid(row=5, column=0, pady=(0, 20), sticky="ew")

        # 進捗バー
        ttk.Label(main_frame, text="進捗:").grid(row=6, column=0, sticky="w", pady=(0, 5))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            main_frame, variable=self.progress_var,
            maximum=100, length=350
        )
        self.progress_bar.grid(row=7, column=0, sticky="ew", pady=(0, 10))

        # ステータス表示
        self.status_var = tk.StringVar(value="待機中")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="gray")
        self.status_label.grid(row=8, column=0, sticky="w")

    def _on_page_mode_change(self):
        """ページ数モード変更時の処理"""
        if self.page_mode.get() == "manual":
            self.page_count_entry.config(state="normal")
        else:
            self.page_count_entry.config(state="disabled")

    def _browse_output(self):
        """出力ファイル選択ダイアログ"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDFファイル", "*.pdf")],
            title="出力ファイルを選択"
        )
        if filepath:
            self.output_var.set(filepath)

    def _validate_inputs(self):
        """入力値の検証"""
        output_path = self.output_var.get().strip()
        if not output_path:
            messagebox.showerror("エラー", "出力ファイルを指定してください。")
            return False

        if self.page_mode.get() == "manual":
            try:
                pages = int(self.page_count_var.get())
                if pages <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("エラー", "ページ数は正の整数で指定してください。")
                return False

        try:
            delay = float(self.delay_var.get())
            if delay < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("エラー", "待機時間は0以上の数値で指定してください。")
            return False

        return True

    def _set_ui_state(self, running):
        """UI要素の有効/無効を切り替え"""
        state = "disabled" if running else "normal"
        self.output_entry.config(state=state)
        self.browse_btn.config(state=state)
        self.page_count_entry.config(state=state if self.page_mode.get() == "manual" else "disabled")

        if running:
            self.start_btn.config(text="キャンセル", command=self._cancel_capture)
        else:
            self.start_btn.config(text="PDF作成開始", command=self._start_capture)

    def _start_capture(self):
        """キャプチャ開始"""
        if not self._validate_inputs():
            return

        self.is_running = True
        self.should_cancel = False
        self._set_ui_state(True)

        # 別スレッドでキャプチャ処理を実行
        self.capture_thread = threading.Thread(target=self._capture_process, daemon=True)
        self.capture_thread.start()

    def _cancel_capture(self):
        """キャプチャをキャンセル"""
        self.should_cancel = True
        self._update_status("キャンセル中...")

    def _update_status(self, message):
        """ステータスを更新（メインスレッドで実行）"""
        self.root.after(0, lambda: self.status_var.set(message))

    def _update_progress(self, value):
        """進捗バーを更新（メインスレッドで実行）"""
        self.root.after(0, lambda: self.progress_var.set(value))

    def _capture_complete(self, success, message):
        """キャプチャ完了時の処理（メインスレッドで実行）"""
        def complete():
            self.is_running = False
            self._set_ui_state(False)
            self.progress_var.set(100 if success else 0)
            self.status_var.set(message)

            if success:
                messagebox.showinfo("完了", message)
            elif "キャンセル" not in message:
                messagebox.showerror("エラー", message)

        self.root.after(0, complete)

    def _capture_process(self):
        """キャプチャ処理（別スレッドで実行）"""
        try:
            # 必要なモジュールをインポート
            try:
                import Quartz
                from Foundation import NSURL
                from PIL import Image
            except ImportError as e:
                self._capture_complete(False, f"必要なモジュールがありません: {e}")
                return

            output_path = self.output_var.get().strip()
            if not output_path.endswith(".pdf"):
                output_path += ".pdf"

            auto_detect = self.page_mode.get() == "auto"
            max_pages = 99999 if auto_detect else int(self.page_count_var.get())
            delay = float(self.delay_var.get())

            # 一時ディレクトリの作成
            temp_dir = tempfile.mkdtemp(prefix="kindle_pdf_")
            image_dir = Path(temp_dir)

            try:
                # Kindleをアクティブ化
                self._update_status("Kindleアプリをアクティブ化中...")
                self._activate_kindle()

                # ウィンドウIDを取得
                self._update_status("KindleウィンドウIDを取得中...")
                window_id = self._get_kindle_window_id()

                if window_id is None:
                    self._capture_complete(False, "Kindleウィンドウが見つかりません。\nKindleアプリを起動して本を開いてください。")
                    return

                # 開始前待機
                self._update_status("3秒後にキャプチャを開始...")
                for i in range(3, 0, -1):
                    if self.should_cancel:
                        self._capture_complete(False, "キャンセルされました")
                        return
                    self._update_status(f"{i}秒後にキャプチャを開始...")
                    time.sleep(1)

                # キャプチャループ
                page_num = 1
                last_hash = None
                same_count = 0

                while page_num <= max_pages:
                    if self.should_cancel:
                        self._capture_complete(False, "キャンセルされました")
                        return

                    filepath = image_dir / f"page_{page_num:04d}.png"

                    # スクリーンショット撮影
                    self._capture_window(window_id, str(filepath))

                    # 自動検出モード: 同じ画像が3回続いたら終了
                    if auto_detect:
                        current_hash = self._get_image_hash(str(filepath))
                        if current_hash == last_hash:
                            same_count += 1
                            if same_count >= 3:
                                # 重複した画像を削除
                                for i in range(same_count):
                                    dup_path = image_dir / f"page_{page_num - i:04d}.png"
                                    if dup_path.exists():
                                        dup_path.unlink()
                                page_num -= same_count
                                self._update_status(f"最後のページを検出（{page_num}ページ）")
                                break
                        else:
                            same_count = 0
                        last_hash = current_hash
                        self._update_status(f"ページ {page_num} をキャプチャ中...")
                    else:
                        progress = (page_num / max_pages) * 90  # 90%までキャプチャ
                        self._update_progress(progress)
                        self._update_status(f"ページ {page_num}/{max_pages} をキャプチャ中...")

                    # ページ送り
                    self._send_page_turn()
                    time.sleep(delay)
                    page_num += 1

                # PDFに結合
                self._update_status("PDFを作成中...")
                self._update_progress(95)
                self._images_to_pdf(image_dir, output_path)

                self._capture_complete(True, f"PDF作成完了: {output_path}")

            finally:
                # 一時ファイルの削除
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            self._capture_complete(False, f"エラーが発生しました: {str(e)}")

    def _get_kindle_window_id(self):
        """KindleアプリのウィンドウIDを取得"""
        import Quartz

        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID
        )

        kindle_windows = []
        for window in window_list:
            owner_name = window.get('kCGWindowOwnerName', '')

            if owner_name == 'Kindle':
                window_id = window.get('kCGWindowNumber')
                bounds = window.get('kCGWindowBounds', {})
                width = bounds.get('Width', 0)
                height = bounds.get('Height', 0)
                if width > 100 and height > 100:
                    kindle_windows.append((window_id, width * height))

        if kindle_windows:
            kindle_windows.sort(key=lambda x: x[1], reverse=True)
            return kindle_windows[0][0]

        return None

    def _activate_kindle(self):
        """Kindleアプリをアクティブ化"""
        script = '''
        tell application "Amazon Kindle"
            activate
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True)
        time.sleep(0.5)

    def _capture_window(self, window_id, filepath):
        """指定ウィンドウのスクリーンショットを撮影"""
        from Foundation import NSURL
        from Quartz import (CGImageDestinationAddImage,
                           CGImageDestinationCreateWithURL,
                           CGImageDestinationFinalize, CGRectNull,
                           CGWindowListCreateImage,
                           kCGWindowImageDefault,
                           kCGWindowListOptionIncludingWindow)

        image = CGWindowListCreateImage(
            CGRectNull,
            kCGWindowListOptionIncludingWindow,
            int(window_id),
            kCGWindowImageDefault
        )

        if image is None:
            raise RuntimeError(f"ウィンドウ {window_id} のキャプチャに失敗しました")

        url = NSURL.fileURLWithPath_(filepath)
        dest = CGImageDestinationCreateWithURL(url, 'public.png', 1, None)
        CGImageDestinationAddImage(dest, image, None)
        CGImageDestinationFinalize(dest)

    def _send_page_turn(self):
        """Kindleで次のページへ移動"""
        script = '''
        tell application "System Events"
            tell process "Kindle"
                key code 124
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True)

    def _get_image_hash(self, filepath):
        """画像ファイルのハッシュ値を取得"""
        from PIL import Image

        with Image.open(filepath) as img:
            return hashlib.md5(img.tobytes()).hexdigest()

    def _images_to_pdf(self, image_dir, output_path):
        """画像ファイルをPDFに結合"""
        from PIL import Image

        image_files = sorted(Path(image_dir).glob("page_*.png"))

        if not image_files:
            raise RuntimeError("画像ファイルが見つかりません")

        images = []
        for img_path in image_files:
            img = Image.open(img_path)
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                images.append(rgb_img)
            else:
                images.append(img.convert('RGB'))

        if images:
            images[0].save(
                output_path,
                save_all=True,
                append_images=images[1:],
                resolution=100.0
            )


def main():
    root = tk.Tk()
    app = KindleToPdfApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
