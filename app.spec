# -*- mode: python ; coding: utf-8 -*-


from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

gpt4all_datas = collect_data_files('gpt4all')
gpt4all_binaries = collect_dynamic_libs('gpt4all')
chroma_hidden = collect_submodules('chromadb')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[] + gpt4all_binaries,
    datas=[
        ('static', 'static/'), 
        ('models', 'models/'), 
        ('chroma_db', 'chroma_db/'),
        ('*.pdf', '.')
    ] + gpt4all_datas,
    hiddenimports=[
        'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 
        'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 
        'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off',
        'langchain_classic.chains.retrieval',
        'langchain_classic.chains.combine_documents.stuff',
        'langchain_classic.chains.combine_documents.base',
        'langchain_classic.chains.llm',
        'pydantic.deprecated.decorator',
        'posthog',
        'bcrypt'
    ] + chroma_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app',
)
