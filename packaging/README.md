# Packaging PlantTrace

Build Windows:

```powershell
.\tools\build_windows.ps1
```

Output:

```text
dist\PlantTrace\PlantTrace.exe
```

Share the whole `dist\PlantTrace` folder. The `.exe` is double-clickable; `_internal` contains the frozen runtime, Qt, the local HTML guide and assets.

Default packaging excludes the optional semantic ML stack to keep the app deterministic and lightweight. OCR still requires a Windows Tesseract installation on the workstation.
