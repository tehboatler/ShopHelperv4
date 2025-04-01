from qpt.executor import CreateExecutableModule as CEM

cem = CEM(
    work_dir='./',
    launcher_py_path='./app.py',
    save_path='./output',
    # requirements_file="./requirements.txt",  # Use the explicit requirements file instead of "auto"
    # To minimize footprint, you might need to specify mode='Mini', check documentation
)

# Execute the build process
cem.make()