"""Local companion for SolarRenderer: encode silence to match the actual AV latent.

Requires the official Enderfga/SolarRenderer custom nodes. No downloaded silence
asset, latent tiling, video padding, or changes to upstream files are needed.
"""
import inspect
import math
import torch


class SolarRendererDynamicSilenceModel:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "model": ("MODEL",),
            "audio_vae": ("VAE",),
            "latent": ("LATENT",),
            "seed": ("INT", {"default": 110, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
        }}

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "patch"
    CATEGORY = "SolarRenderer/local"
    DESCRIPTION = "Encode real silence matching the AV latent duration; reuse the official SolarRenderer audio wrapper."

    def patch(self, model, audio_vae, latent, seed):
        import nodes
        import comfy.patcher_extension

        official = nodes.NODE_CLASS_MAPPINGS.get("SolarRendererModel")
        if official is None:
            raise RuntimeError("Install Enderfga/SolarRenderer and restart ComfyUI first.")
        module = inspect.getmodule(official)
        wrapper_class = getattr(module, "_SilentSoundtrack", None)
        if wrapper_class is None:
            raise RuntimeError("SolarRenderer's audio wrapper API has changed; update this companion before rendering.")

        samples = latent["samples"]
        if not getattr(samples, "is_nested", False) or len(samples.tensors) != 2:
            raise ValueError("Expected a MiniMax H3 nested video/audio latent.")
        target = samples.tensors[1]
        if target.ndim != 4 or tuple(target.shape[1:3]) != (32, 2):
            raise ValueError("Expected H3 audio latent [B, 32, 2, T].")
        count = int(target.shape[-1])
        if count <= 0:
            raise ValueError("Empty audio latent.")
        rate = int(getattr(audio_vae, "audio_sample_rate", 32000))
        # H3 audio latents are 40 Hz. One extra second covers encoder boundary
        # rounding; only the actual target length reaches the sampling wrapper.
        waveform = torch.zeros((1, math.ceil((count / 40.0 + 1.0) * rate), 2), dtype=torch.float32)
        with torch.inference_mode():
            silence = audio_vae.encode(waveform)
        if silence.ndim != 4 or tuple(silence.shape[1:3]) != (32, 2):
            raise ValueError("The selected audio VAE did not return H3 audio latents.")
        if silence.shape[-1] < count:
            raise ValueError(f"Audio VAE returned {silence.shape[-1]} tokens; need {count}. No padding is applied.")
        silence = silence[..., :count].detach().to(device="cpu", dtype=torch.float32).contiguous()
        patched = model.clone()
        patched.add_wrapper(comfy.patcher_extension.WrappersMP.DIFFUSION_MODEL,
                            wrapper_class(silence, int(seed)))
        return (patched,)


NODE_CLASS_MAPPINGS = {"SolarRendererDynamicSilenceModel": SolarRendererDynamicSilenceModel}
NODE_DISPLAY_NAME_MAPPINGS = {"SolarRendererDynamicSilenceModel": "SolarRenderer Model - Dynamic Silence (local)"}
