# ComfyUI SolarRenderer Dynamic Silence

A small companion node for [SolarRenderer](https://github.com/Enderfga/SolarRenderer) in ComfyUI. It encodes silent audio for the duration of the actual MiniMax H3 audio/video latent, then reuses SolarRenderer's silent-soundtrack sampling wrapper.

## Why this exists

The upstream implementation inspected during development loads a pre-encoded silence asset covering 170 video frames and raises an error when the target audio latent is longer. This companion replaces that fixed-length preparation with an audio VAE encode of silence.

It does not extend, duplicate, interpolate, or retime video frames. The structure conditioning and sampler still generate the requested video. It does not make arbitrary durations or resolutions supported, and it does not change SolarRenderer's training distribution.

**Status:** experimental, with four completed 175-frame motion-transfer tests at 24 fps in one local Windows / RTX 5090 environment. See [validation details](VALIDATION.md). This is not a universal compatibility or quality guarantee.

## Requirements

- ComfyUI with native MiniMax H3 support.
- The official [Enderfga/SolarRenderer custom nodes](https://github.com/Enderfga/SolarRenderer/tree/main/comfyui).
- A compatible MiniMax H3 audio VAE. The reported runs used `minimax_h3_audio_vae_fp32.safetensors`.
- The usual H3 model, video VAE, text encoder, and SolarRenderer LoRAs required by your workflow.

PyTorch comes from the existing ComfyUI environment. No additional pip packages or model downloads are performed by this node. No weights are bundled.

The node depends on the private `_SilentSoundtrack` class in the module registering `SolarRendererModel`. If upstream changes that API, this companion may need an update. It checks for that class and fails with an explicit message when unavailable.

## Installation

1. Install the official SolarRenderer repository in `ComfyUI/custom_nodes/SolarRenderer`.
2. Put this repository folder in `ComfyUI/custom_nodes/ComfyUI-SolarRenderer-DynamicSilence`.
3. Restart ComfyUI.

The directory must look like this:

```text
ComfyUI/
  custom_nodes/
    SolarRenderer/
    ComfyUI-SolarRenderer-DynamicSilence/
      __init__.py
      README.md
      LICENSE
```

On Windows, avoid an extra nested folder when extracting a ZIP. `__init__.py` must be directly inside the custom-node folder.

Search for **SolarRenderer Model - Dynamic Silence (local)** in the node menu. The internal node ID is `SolarRendererDynamicSilenceModel`.

## Connections

Replace the original **SolarRenderer Model (silent soundtrack)** node with this node. Do not chain both silence patches.

| Input | Connect |
|---|---|
| `model` | The H3 model after the SolarRenderer LoRAs and applicable model settings |
| `audio_vae` | A loaded compatible H3 audio VAE |
| `latent` | The AV latent returned by SolarRenderer Structure to Video |
| `seed` | A fixed seed for the held audio-noise draw |

Connect the resulting **MODEL** to the sampler's guider. Continue connecting the conditioning and latent from SolarRenderer Structure to Video to the guider and sampler as usual.

```text
H3 model + SolarRenderer LoRAs --------> Dynamic Silence.model
H3 audio VAE ------------------------> Dynamic Silence.audio_vae
SolarRenderer conditioning LATENT ----> Dynamic Silence.latent
Dynamic Silence MODEL ---------------> BasicGuider.model
SolarRenderer conditioning POSITIVE --> BasicGuider.conditioning
SolarRenderer conditioning LATENT ----> Sampler.latent_image
```

With split sampling, both samplers should use the same patched guider. This node does not choose samplers or sigma schedules. Its seed controls held audio noise, not the main video's RandomNoise node.

The node does not add a final audio track to saved videos. Audio saving remains the responsibility of the workflow.

## How it works

1. Read the audio token length from the supplied H3 nested AV latent, shaped `[B, 32, 2, T]` on the audio side.
2. Construct a stereo zero waveform using the audio VAE's sample rate and H3's 40 Hz audio latent clock, with one second of encoding margin.
3. Encode it through the audio VAE. Silent waveform samples are encoded; the node does not assume that zero latent values represent silence.
4. Trim the encoded silence to the required token count. If it is too short or has the wrong shape, stop with an error instead of padding it.
5. Clone the model and attach the official SolarRenderer silent-soundtrack wrapper with that encoded silence.

For 175 frames at 24 fps, the current H3 latent convention requests 292 audio tokens. The extra waveform margin is only used during audio encoding; it adds no video frames.

## Limitations and troubleshooting

- **Node missing:** check the folder nesting and restart ComfyUI.
- **Install SolarRenderer first:** the official `SolarRendererModel` must be registered successfully. Check ComfyUI's startup log for import failures.
- **Wrapper API changed:** use a compatible upstream version or update this companion. Do not remove the check to force execution.
- **Wrong latent shape:** use the full H3 AV latent, before Separate AV Latent, not a video-only or RelayVSR latent.
- **Wrong audio VAE output:** select an H3 audio VAE, not the video VAE.
- **Short encoded silence:** the node deliberately refuses latent padding. Report the audio VAE version and tensor dimensions.
- **Memory:** longer video still costs more memory. This node only addresses silence preparation, not transformer memory or temporal consistency.

Encoding silence adds a VAE operation and may cause model offloading. The dynamically encoded silence is not established as bitwise identical to the original baked asset. Multi-batch rendering and upstream versions beyond those used in the reported runs have not been validated.

## Credits and license

Independent companion for [SolarRenderer](https://github.com/Enderfga/SolarRenderer), built on [ComfyUI](https://github.com/Comfy-Org/ComfyUI) and MiniMax H3. It is not an official SolarRenderer release and does not include upstream source or model weights.

This repository's companion code and documentation are provided under the [MIT License](LICENSE). SolarRenderer, ComfyUI, MiniMax H3, and model weights retain their own licenses.
