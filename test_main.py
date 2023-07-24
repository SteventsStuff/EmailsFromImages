import os
from glob import iglob

import main


def run_all() -> None:
    for filepath in iglob('input/*/*', recursive=True):
        input_path = filepath
        tmp_path = filepath.split('/')
        output_filename = tmp_path[-1].split('.')[0] + '.txt'
        output_dir_path = 'output/' + '/'.join(tmp_path[1:-1])
        output_path = output_dir_path + f'/{output_filename}'

        if not os.path.exists(output_dir_path):
            os.makedirs(output_dir_path)

        print(f'Calling script with --input {input_path} --output {output_path}')
        main.main(['--input', input_path, '--output', output_path])
        print('\n\n\n')
    else:
        print('Done')


if __name__ == '__main__':
    run_all()
