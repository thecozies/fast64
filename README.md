# Fast64

This requires Blender 3.2+.

Forked from [kurethedead/fast64 on BitBucket](https://bitbucket.org/kurethedead/fast64/src).

![alt-text](/images/mario_running.gif)

This is a Blender plugin that allows one to export F3D display lists. It also has the ability to export assets for Super Mario 64 and Ocarina of Time decompilation projects. It supports custom color combiners / geometry modes / etc. It is also possible to use exported C code in homebrew applications.

![alt-text](/images/mat_inspector.png)

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Game specific and development documentation](#game-specific-and-development-documentation)
- [Credits](#credits)
- [Discord Server](#discord-server)
- [Installation](#installation)
- [Tool Locations](#tool-locations)
- [F3D Materials](#f3d-materials)
  - [Vertex Colors](#vertex-colors)
  - [Large Texture Mode](#large-texture-mode)
  - [Decomp vs Homebrew Compatibility](#decomp-vs-homebrew-compatibility)
  - [Converting To F3D V5 Materials](#converting-to-f3d-v5-materials)
  - [Updater](#updater)

## Game specific and development documentation

- [Super Mario 64](/fast64_internal/sm64/README.md)
- [Ocarina Of Time](/fast64_internal/oot/README.md)
- [Fast64 Development](/development.md)

## Credits

Thanks to anonymous_moose, Cheezepin, Rovert, and especially InTheBeef for testing.
Thanks to InTheBeef for LowPolySkinnedMario.

## Discord Server

We have a Discord server for support as well as development [here](https://discord.gg/ny7PDcN2x8).

## Installation

Download the repository as a zip file. In Blender, go to Edit -> Preferences -> Add-Ons and click the "Install" button to install the plugin from the zip file. Find the Fast64 addon in the addon list and enable it. If it does not show up, go to Edit -> Preferences -> Save&Load and make sure 'Auto Run Python Scripts' is enabled.

## Tool Locations

The tools can be found in the properties sidebar under the 'Fast64' tab (toggled by pressing N).
The F3D material inspector can be found in the properties editor under the material tab.

## F3D Materials

Any exported mesh must use an F3D Material, which can be added by the 'Create F3D Material' button in the material inspector window. You CANNOT use regular blender materials. If you have a model with Principled BSDF materials, you can use the Principled BSDF to F3D conversion operator to automatically convert them. The image in the "Base Color" slot will be set as texture 0, while the image in the "Subsurface Color" slot will be set as texture 1.

### Vertex Colors

To use vertex colors, select a vertex colored texture preset and there will be two Face Corner Color Attributes in your mesh named 'Col' and 'Alpha'. The alpha layer will use the greyscale value of the vertex color to determine alpha.

If you are new to Blender 3.2+, the selected color attribute will be chosen from the active attribute under **Color Attribute** panel and **NOT** the active attribute in the **Attribute** panel. See below:

![Color Attributes](/images/color_attributes.png)

Note: enabling "Fog" will disable your vertex colors, and will be replaced with the fog coefficient in `Shade Alpha`, this is a hardware limitation that is emulated in Fast64.

### Large Texture Mode

In F3D material properties, you can enable "Large Texture Mode". This will let you use textures up to 1024x1024 as long as each triangle in the mesh has UVs that can fit within a single tile load. Fast64 will categorize triangles into shared tile loads and load the portion of the texture when necessary.

### Decomp vs Homebrew Compatibility

There may occur cases where code is formatted differently based on the code use case. In the tools panel under the Fast64 File Settings subheader, you can toggle homebrew compatibility.

### Converting To F3D V5 Materials

V5 Materials are currently required in Fast64. If you have a project containing materials created prior to V5, you will see a popup upon opening the project:

![Upgrade Modal](/images/detect_upgrades.png)

Once you hit **OK**, Fast64 will upgrade all of your materials, and your old materials will be removed from your meshes. If you don't see this modal and need to upgrade, you can use the "Recreate F3D Materials As V5" operator in the Fast64 tab in 3D view:

![Material Converter](/images/material_converter.png)

Then go to the outliner, change the display mode to "Orphan Data" (broken heart icon), then click "Purge" in the top right corner. Purge multiple times until all of the old node groups are gone.

![Purge](/images/orphan_data.png)

### Updater

Fast64 features an updater ([CGCookie/blender-addon-updater](https://github.com/CGCookie/blender-addon-updater)).

It can be found in the addon preferences:

![How the updater in the addon preferences looks, right after addon install](/images/updater_initially.png)

Click the "Check now for fast64 update" button to check for updates.

![Updater preferences after clicking the "check for updates" button](/images/updater_after_check.png)

Click "Install main / old version" and choose "Main" if it isn't already selected:

![Updater: install main](/images/updater_install_main.png)

Click OK, there should be a message "Addon successfully installed" and prompting you to restart Blender:

![Updater: successful install, must restart](/images/updater_success_restart.png)

Clicking the red button will close Blender. After restarting, fast64 will be up-to-date with the latest main revision.
