# Kindle to PDF

Kindle for Macアプリのスクリーンショットを自動で撮影し、PDFに結合するツール。

GUI版（アプリ）とCLI版の両方が利用可能です。

## 必要なもの

- macOS
- Python 3.x
- Amazon Kindle アプリ（App Store版）
- Pillow (`pip install Pillow`)
- pyobjc-framework-Quartz (`pip install pyobjc-framework-Quartz`)

## セットアップ

1. 依存パッケージをインストール

```bash
pip install Pillow pyobjc-framework-Quartz
```

2. システム権限を付与

システム設定 > プライバシーとセキュリティ で以下を許可:
- **アクセシビリティ**: ターミナル（またはiTerm等）またはKindle to PDF.app
- **画面収録**: ターミナル（またはiTerm等）またはKindle to PDF.app

## GUI版（推奨）

### GUIで実行

```bash
python kindle_to_pdf_gui.py
```

### macOSアプリとしてビルド

1. PyInstallerをインストール

```bash
pip install pyinstaller
```

2. アプリをビルド

```bash
pyinstaller --name "Kindle to PDF" --windowed --onedir --noconfirm --icon icon.icns kindle_to_pdf_gui.py
```

3. `dist/Kindle to PDF.app` が生成されます

4. （オプション）Applicationsフォルダにコピー

```bash
cp -R "dist/Kindle to PDF.app" /Applications/
```

### アプリの使い方

1. `Kindle to PDF.app` をダブルクリックで起動
2. 出力ファイル名を「参照...」ボタンで指定
3. ページ数を選択（自動検出推奨）
4. 「PDF作成開始」をクリック
5. 3秒後にキャプチャが開始される
6. 完了するとPDFが生成される

### 初回起動時の注意

- **「開発元不明」警告**: 右クリック → 「開く」で回避可能
- **権限ダイアログ**: 「アクセシビリティ」「画面収録」の許可が必要

## CLI版

1. Amazon Kindleアプリで本を開き、最初のページを表示
2. ターミナルでスクリプトを実行

```bash
# 全ページを自動でPDF化（推奨）
python kindle_to_pdf.py -o mybook.pdf

# ページ数を指定する場合
python kindle_to_pdf.py -p 200 -o mybook.pdf
```

3. 3秒後にキャプチャが開始される
4. 完了するとPDFが生成される

### オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|-----------|
| `--output` | `-o` | 出力PDFファイル名（必須） | - |
| `--pages` | `-p` | キャプチャするページ数（省略時は自動検出） | 自動 |
| `--delay` | `-d` | ページ送り後の待機秒数 | 1.0 |
| `--start-page` | `-s` | 開始ページ番号（途中再開用） | 1 |
| `--keep-images` | `-k` | 終了後も画像を保持 | False |

### 使用例

```bash
# 全ページを自動検出してPDF化
python kindle_to_pdf.py -o my_book.pdf

# ページ数を指定
python kindle_to_pdf.py -p 300 -o my_book.pdf

# ページ描画が遅い場合（待機時間を増やす）
python kindle_to_pdf.py -o my_book.pdf -d 1.5

# 途中で中断した場合の再開（100ページ目から）
python kindle_to_pdf.py -p 300 -o my_book.pdf -s 100

# 画像も保持したい場合
python kindle_to_pdf.py -o my_book.pdf -k
```

### 自動検出モードについて

`--pages`を省略すると自動検出モードになります。3回連続で同じページが検出されると最後のページと判断して終了します。

## 注意事項

- 実行中はKindleウィンドウを動かしたり最小化しないでください
- キャプチャ中は他の作業を控えることを推奨します
- Ctrl+C で中断できます。`--start-page` オプションで途中から再開可能です

## トラブルシューティング

### 「Kindleウィンドウが見つかりません」エラー

- Amazon Kindleアプリが起動しているか確認
- 本を開いてウィンドウが表示されているか確認

### スクリーンショットが撮れない

- **画面収録**の権限が付与されているか確認
- システム設定 > プライバシーとセキュリティ > 画面収録

### ページ送りができない

- **アクセシビリティ**の権限が付与されているか確認
- システム設定 > プライバシーとセキュリティ > アクセシビリティ

### ページがずれる・抜ける

- `--delay` オプションで待機時間を増やしてみてください（例: `-d 2.0`）
