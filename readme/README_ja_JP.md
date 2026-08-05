# Shisa AI Tools for Dify

Shisa AIの高度な音声機能と翻訳APIをDify Workflow／Chatflowから利用するためのToolsプラグインです。

## ツール

- **TTS音声一覧**: 現在の音声、UUID、言語、対応形式、ストリーミング対応状況を動的に取得します。
- **音声生成**: 読みやすい音声説明またはUUIDを使い、対応するMP3、WAV、OGG、FLAC、PCMを完了ファイルとして生成します。
- **テキスト翻訳**: Shisa Translation APIを使い、日本語と英語の間を翻訳します。

Dify Toolノードは同期実行のため、音声生成と翻訳では非ストリーミングの完了レスポンスを使用します。

APIキーは [Shisa Platform](https://platform.shisa.ai/) で取得してください。料金、利用上限、音声カタログ、サービス提供状況などの最新情報は、[Shisa Platform](https://platform.shisa.ai/) と [公式ドキュメント](https://docs.shisa.ai/) を確認してください。
