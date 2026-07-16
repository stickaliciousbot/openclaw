# M10A Package Preservation Drift Root Cause

Status: `PASS_M10A_PACKAGE_PRESERVATION_DRIFT_ROOT_CAUSE_CLASSIFIED`

Classification: `INSTALL_COPIED_UNEXPECTED_M8_DIST`

Secondary classifications: `TARBALL_INCLUDED_UNEXPECTED_M8_DIST`, `BUILD_REGENERATED_PRESERVED_M8_DIST`.

The full npm tarball contained M8 at `753fade05d957fb295dcf33a7beaec7a89d6b977e750c937e26a9cd7ad18b0ef`, while the restored installed runtime requires M8 at `27116a4374b699b7e98bc8ec9be98f3584bc14a8ca740d0723316deaa66088db`. Installing the whole tarball copied the regenerated M8 dist file. No M10A/M8 entry collision was found.
