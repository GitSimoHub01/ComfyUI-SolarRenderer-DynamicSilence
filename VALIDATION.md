# Validation record

Recorded on 2026-11-23. Test media and source workflows are not distributed.

## Completed local generation tests

The user reported successful complete generation runs. Saved workflow metadata was inspected to identify the actual settings, and the base and final video streams were read to count frames. Each of the four runs below contained **175 frames at 24 fps** in both the base and final outputs.

| SolarRenderer weights | First-pass steps | Split | Samplers | Completion |
|---|---:|---|---|---|
| Comfy-converted `fro_dyn99` four-step + Control | 4 | 2 + 2 | LCM / LCM | Base and final verified |
| Comfy-converted full four-step + Control | 4 | 2 + 2 | LCM / LCM | Base and final verified |
| Comfy-converted full Control; four-step LoRA bypassed | 30 | 20 + 10 | LCM / LCM | Base and final verified |
| Comfy-converted full four-step + Control | 6 | 4 + 2 | LCM / ER_SDE | Base and final verified |

These are execution observations, not recommended sampling recipes or evidence of visual superiority. In particular, the Control-only run really used LCM in both halves; its successful completion is not an endorsement of that sampler for non-distilled generation.

For the fourth run (six steps, 4 LCM + 2 ER_SDE), the user reported no noticeable visual improvement. This is a subjective user observation, not a measured quality comparison. The completed run supports execution compatibility for this configuration; it does not establish a benefit from additional steps or mixed samplers.

Environment: Windows, RTX 5090, native MiniMax H3 support, H3 FP32 audio VAE. Exact ComfyUI and SolarRenderer commit identifiers were not recorded for these runs, so compatibility cannot be attributed to a pinned version.

## Isolated CPU checks

With a simulated audio encoder, model patcher, and upstream wrapper:

- Target lengths corresponding to 158, 175, and 192 video frames produced the expected audio token lengths.
- The encoded values were preserved when trimming; they were not replaced by zero latents.
- The wrapper received the selected seed.
- An encoder output shorter than the target was rejected.

These checks validate local shape and routing logic, not audio-VAE numerical equivalence or end-to-end rendering. The four real generation runs above provide separate integration evidence.

## Not established

- Visual quality improvements over the original silence asset.
- Arbitrary-length, multi-batch, or cross-platform operation.
- Bitwise equivalence to SolarRenderer's bundled silence.
- Compatibility with future changes to the private `_SilentSoundtrack` API.
