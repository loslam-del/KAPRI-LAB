# Android update compatibility

Current KAPRI package identity:
- applicationId: com.example.screenai
- versionCode: maintain in source/app/build.gradle.kts and increase for each release.

## Why Android may report an app conflict

An in-place Android update requires the same application ID and a compatible signing certificate.
The current K.A.P.R.И. workflow builds assembleDebug on a fresh GitHub-hosted runner. The Android debug keystore is generated on that runner and is not a persistent release identity. A later run can therefore produce an APK signed with a different debug certificate. Android rejects it as an update and may report a package/signature conflict.

## Migration limitation

A new signing key cannot retroactively match an APK already installed with a different key. To update the currently installed app without uninstalling, the original signing key must be recovered and reused. If it is unavailable, a one-time uninstall/reinstall is required to migrate to a new stable signing key; app data may be lost. Do not uninstall until important data is backed up.

## Stable release signing

For future builds, create and retain one private release keystore and configure GitHub Actions repository secrets: KAPRI_KEYSTORE_BASE64, KAPRI_KEYSTORE_PASSWORD, KAPRI_KEY_ALIAS, and KAPRI_KEY_PASSWORD. Never commit the keystore or passwords or print secrets in workflow logs.

Normal in-place updates with the same package identity and signing certificate usually preserve app data and existing grants. New permissions and special-access settings may still require user action.
