<h1 align="center">
	FLATSAT PLATFORM V2.0 - HARDWARE
	<br>
</h1>

<h4 align="center">Hardware project of the FlatSat Platform 2.0, designed and developed by SpaceLab.</h4>

<p align="center">
    <a href="https://github.com/spacelab-ufsc/spacelab#versioning"><img alt="Static Badge" src="https://img.shields.io/badge/status-in_development-red"></a>
    <a href="https://github.com/spacelab-ufsc/flatsat-platform2-hardware/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/spacelab-ufsc/flatsat-platform2-hardware"></a>
    <a href="https://github.com/spacelab-ufsc/flatsat-platform2-hardware/commits/main"><img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/spacelab-ufsc/flatsat-platform2-hardware"></a>
    <a href="https://github.com/spacelab-ufsc/flatsat-platform2-hardware/issues"><img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues/spacelab-ufsc/flatsat-platform2-hardware"></a>
    <a href="https://github.com/spacelab-ufsc/flatsat-platform2-hardware/pulls"><img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues-pr/spacelab-ufsc/flatsat-platform2-hardware"></a>
    <a href="https://github.com/spacelab-ufsc/flatsat-platform2-hardware/graphs/contributors"><img alt="GitHub contributors" src="https://img.shields.io/github/contributors/spacelab-ufsc/flatsat-platform2-hardware"></a>
    <a href="https://www.kicad.org/"><img alt="Static Badge" src="https://img.shields.io/badge/CAD_tool-KiCad_9.0-blue"></a>
    <a href="#license"><img alt="Static Badge" src="https://img.shields.io/badge/license-CERN--OHL--S--2.0-yellow"></a>
</p>

<details>
    <summary>Summary</summary>
    <ol>
        <li>
            <a href="#overview">Overview</a>
        </li>
        <li>
            <a href="#repository-organization">Repository Organization</a>
        </li>
        <li>
            <a href="#license">License</a>
        </li>
        <li>
            <a href="#releases">Releases</a>
        </li>
        <li>
            <a href="#notes">Notes</a>
        </li>
        <li>
            <a href="#references">References</a>
        </li>
    </ol>
</details>

## Overview
The **FlatSat Platform 2.0** is a testbench for testing the main SpaceLab's subsystems, but can be adapted for other CubeSat missions. A FlatSat is an electrical model of the satellite with the subsystems assembled side by side over a workbench that can be mounted during the V&V [[1]](#1). They offer an easier, faster and safer way for testing subsystems before assembly into the final structure of a CubeSat. It can be used in combination with the hardware-in-the-loop (HIL) technique, which justifies the usage of a built-in MicroZed and sensors. Moreover, it supports up to 6 modules. This platform is intended to function as an electrical ground support equipment (EGSE) for the SpaceLab team, leveraging the MicroZed, sensors, and future daughterboards to emulate and simulate diverse mission scenarios. Additionally, it facilitates comprehensive system-level and subsystem-level testing. The FlatSat Platform itself is presented in [[2]](#2).

This repository contains the hardware project of the FlatSat Platform 2.0 (schematics, PCB layout, libraries and fabrication files), developed in KiCad.

<p align="center">
    <img src="https:https://github.com/spacelab-ufsc/flatsat-platform2-hardware/blob/fix/altium-to-kicad-convert/outputs/top_pcb.png">
</p>

<p align="center">
    <a href="https://github.com/spacelab-ufsc/flatsat-platform2-hardware/issues/new?labels=bug"><img alt="Static Badge" src="https://img.shields.io/badge/Report_a_bug-red"></a>
    <a href="https://github.com/spacelab-ufsc/flatsat-platform2-hardware/issues/new?labels=enhancement"><img alt="Static Badge" src="https://img.shields.io/badge/Request_a_feature-yellow"></a>
    <a href="https://github.com/spacelab-ufsc/flatsat-platform2-hardware/issues/new?labels=question,help+wanted"><img alt="Static Badge" src="https://img.shields.io/badge/Request_more_information_or_help-green"></a>
</p>

## Repository Organization
`sources`: KiCad project (schematics, PCB layout, project settings and library tables).

`lib`: Project libraries: symbols (`*.kicad_sym`), footprints (`lib.pretty`), 3D models (`lib.3dshapes`) and the symbol generator (`lib.gen`).

`altium_import`: Symbols, footprints and 3D models converted from the original Altium project.

`fab`: Fabrication files (Gerbers, drill and placement files) and the script that packages them.

`outputs`: Project outputs, such as schematic PDF and board renders.

`kibot.yml`: [KiBot](https://github.com/INTI-CMNB/KiBot) configuration for generating the outputs.

## License
This repository is open-source under the CERN Open Hardware Licence Version 2 - Strongly Reciprocal (CERN-OHL-S-2.0).

## Releases
The FlatSat Platform hardware, firmware and documentation releases are synchronized in order to guarantee compatibility. Using different versions might lead to unpredictable behavior. Refer to the [documentation](https://github.com/spacelab-ufsc/flatsat-platform2) for compatibility notes.

## Notes
Related repositories: [FlatSat Platform 2.0](https://github.com/spacelab-ufsc/flatsat-platform2) (main repository and documentation) and [FlatSat Platform 2.0 Firmware](https://github.com/spacelab-ufsc/flatsat-platform2-firmware).

For more info about the SpaceLab, access our [GitHub](https://github.com/spacelab-ufsc/spacelab), [Linkedin](https://br.linkedin.com/company/spacelab-ufsc) or our [website](https://spacelab.ufsc.br/en/home/).

## References
<a id="1">[1]</a> J. C. E. Barcellos, A. W. Spengler, L. O. Seman, R. D. C. e. Silva, H. P. Roldán and E. A. Bezerra, "FlatSat Platforms for Small Satellites: A Systematic Mapping and Classification," in IEEE Journal on Miniaturization for Air and Space Systems, vol. 4, no. 2, pp. 186-198, June 2023, doi: 10.1109/JMASS.2023.3249044. Available [here](https://ieeexplore.ieee.org/document/10052660).

<a id="2">[2]</a> J. C. E. Barcellos, C. A. P. Freitas, V. N. Kürschner, V. G. P. Curtarelli, E. A. Bezerra; A. W. Spengler, "An Open-Source, Reconfigurable FlatSat Platform for CubeSat Verification: Design and Validation," in IEEE Journal on Miniaturization for Air and Space Systems, vol. 7, no. 3, pp. 334 - 347, September 2026, doi:10.1109/JMASS.2026.3706017. Available [here](https://ieeexplore.ieee.org/document/11574658).
