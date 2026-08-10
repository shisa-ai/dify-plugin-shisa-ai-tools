# Privacy

Shisa AI Tools sends user-provided audio, text, and selected transcription, translation, or speech-synthesis parameters to the Shisa AI API to perform the requested operation.

## What is collected and transmitted

- Audio uploaded for transcription or speech synthesis
- Text submitted for translation or transcription
- Selected transcription, translation, or speech-synthesis parameters
- Voice catalogue requests (voice identifiers and request metadata)

## How it is used

Data is transmitted only to perform the operation the user requested. Credentials are used only for authenticated API requests and are not intentionally logged or included in tool output. Translation account-balance data returned by the API is not included in tool output. The Transcribe Audio tool returns transcription metadata supplied by the API (such as language and confidence) as structured tool output.

## Where it goes

Data is sent to the Shisa AI API. Service-side data handling is governed by the [Shisa AI privacy policy](https://platform.shisa.ai/en/terms/privacy) and [terms](https://platform.shisa.ai/en/terms/conditions).

The plugin itself does not store, log, or share this content with any party other than Shisa AI. For paid API access, Shisa processes user content solely to deliver the requested service and does not use it to train models without explicit written permission; see the Shisa AI privacy policy for details.
