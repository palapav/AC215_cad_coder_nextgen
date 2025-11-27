# """Public exports for the llava package.

# Try to import the commonly-used model classes from the package-level
# `model` export. If that fails (for example because `model.__init__`
# silently swallowed an import error), try to import the implementation
# directly from the language_model submodule and raise a clear error
# if neither works.
# """

# try:
# 	from .model import LlavaLlamaForCausalLM, LlavaConfig
# except Exception:
# 	# fallback to direct import from submodule to avoid relying on
# 	# a package `model` that may silently swallow errors.
# 	try:
# 		from .model.language_model.llava_llama import LlavaLlamaForCausalLM, LlavaConfig
# 	except Exception as e:
# 		# Raise an informative ImportError so callers see the root cause
# 		raise ImportError(
# 			"Failed to import LlavaLlamaForCausalLM from llava.model; "
# 			"check that dependencies are installed and that the submodules "
# 			"import correctly. Original error: %r" % e
# 		) from e

# __all__ = ["LlavaLlamaForCausalLM", "LlavaConfig"]
from .model import LlavaLlamaForCausalLM