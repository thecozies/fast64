# Fast64 Development

If you'd like to develop in VSCode, follow this tutorial to get proper autocomplete. Skip the linter for now, we'll need to make sure the entire project gets linted before enabling autosave linting because the changes will be massive.
https://b3d.interplanety.org/en/using-microsoft-visual-studio-code-as-external-ide-for-writing-blender-scripts-add-ons/

## Formatting

We use [Black](https://black.readthedocs.io/en/stable/index.html).

To make VS Code use it, change the `python.formatting.provider` setting to "black". VS Code will ask you to install Black if not already installed.

To format the whole repo, run `black .` (or `python3 -m black .` depending on how it is installed) from the root of the repo.

The (minimal) configuration for Black is in `/pyproject.toml`.

## Updater notes

Be careful if testing the updater when using git, it may mess up the .git folder in some cases.

Also see the extensive documentation in the https://github.com/CGCookie/blender-addon-updater README.

The "Update directly to main" button uses `bl_info["version"]` as the current version, and versions parsed from git tags as other versions. This means that to create a new version, the `bl_info` version should be bumped and a corresponding tag should be created (for example `"version": (1, 0, 2),` and a `v1.0.2` tag). This tag will then be available to update to, if it denotes a version that is more recent than the current version.

The "Install main / old version" button will install the latest revision from the `main` branch.

## Adding new menu panels

All new game specific panels should base off of the panels defined in [fast64_internal/panels.py](/fast64_internal/panels.py). These are automatically set up to be visible or not depending `scene.gameEditorMode` (either `"SM64"`/`"OOT"`).

### SM64 Panels

In order to reduce excess noise in SM64 options, you may supply `goal` (see options in `sm64GoalTypeEnum`), in order to show or hide panels depending on what the user has specified their goal as. There is also a `decomp_only` option, which will hide the panel whenever the exportType is not `C`.

### OOT Panels

Currently there isn't any special functionality in OOT panels outside of hiding when SM64 isn't selected.
