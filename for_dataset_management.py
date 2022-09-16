#-*- coding:utf-8 -*-
# Juyeong 220118
# 데이터셋 관리 관련 코드 모듈화

import json
import os
import glob
import shutil
import xml.etree.ElementTree as elemTree


## Anntoation 형식 coco->YOLO 변환
def convert_coco_to_YOLO(img_size, xmin, ymin, w, h): #img_size : tuple

    dw = 1. / img_size[0]
    dh = 1. / img_size[1]

    xmax = xmin + w
    ymax = ymin + h
    
    x = (xmin + xmax) / 2.0
    y = (ymin + ymax) / 2.0

    w = xmax - xmin
    h = ymax - ymin

    bbox_x = round(x * dw, 6)
    bbox_y = round(y * dh, 6)
    bbox_w = round(w * dw, 6)
    bbox_h = round(h * dh, 6)

    bbox = str(bbox_x) + ' ' + str(bbox_y) + ' ' + str(bbox_w) + ' ' + str(bbox_h)

    return bbox


## 211210
## xml 파일을 입력받아 YOLO 형식의 txt 파일로 변환, NIA 과제에 맞춰져 있음
def convert_xml_to_txt(xmlfile):
    #내가 필요한 거 : classID, bbox coord(x_center, y_center, w, h)

    ## 총 25개 클래스 -> class 목록을 txt로 받으면 dict로 변환하도록 코드 변환 필요!
    class_dict = {
        'Person'                    : 0,
        'Animal'                    : 1,
        'Vehicle'                   : 2,
        'Wheeled object'            : 3,
        'Movable Object'            : 4,
        "Fixed Object"              : 5,
        "Obstruction"               : 6,
        "Automatic Door"            : 7,
        "Automatic Revolving Door"  : 8,
        "Sliding Door"              : 9,
        "Hinger Door"               : 10,
        "Manual Revolving Door"     : 11,
        "Escalator"                 : 12,
        "Elevator"                  : 13,
        "Address"                   : 14,
        "Sign"                      : 15,
        "Screen"                    : 16,
        "Up"                        : 17,
        "Down"                      : 18,
        "Open"                      : 19,
        "Close"                     : 20,
        "Floor Button"              : 21,
        "Emergency Button"          : 22,
        "Handle"                    : 23,
        "Bell"                      : 24
    }

    tree = elemTree.parse(xmlfile)
    root = tree.getroot()

    ## txt file name
    fname = root.find('filename').text
    fname = fname[:-4] #확장자 삭제
    txtname = '../' + fname + '.txt'

    ## image size
    size = root.find('size')     #이렇게 하면 '노드'를 가져온다.
    img_size = (int(size[0].text), int(size[1].text))
    print(img_size) #(1920,1080)

    obj = root.findall('object')
    # print(obj[0].find('name').text)

    with open(txtname, 'w') as f:
        for i in range(len(obj)):

            obj_name = obj[i].find('name').text
            class_id = str(class_dict[obj_name])
            print(class_id)
            
            xmin = int(obj[i].find('bndbox').find('xmin').text)
            ymin = int(obj[i].find('bndbox').find('ymin').text)
            w = int(obj[i].find('bndbox').find('xmax').text)
            h = int(obj[i].find('bndbox').find('ymax').text)
            print(xmin, ymin, w, h)

            bbox_line = convert2YOLOann(img_size, xmin, ymin, w, h)
            line = class_id + ' ' + bbox_line + '\n'
            # print(line)
            
            f.write(line)


## 211209 
## json 파일을 입력받아 이미지 한 장 당 한 개의 txt 파일로 변환, coco->YOLO 형식으로 변환됨
def convert_json_to_txt(jsonfile, dst):
    ## Flow ##
    ## 입력받은 json파일 열고 데이터를 받아옴 image/ann 목록 -> 리스트
    ## 이미지 파일과 같은 이름의 텍스트 파일(annotation of YOLO) 생성
    ## json에서 ann에 해당되는 리스트에 접근해서 classID, xmin, ymin, w, h 파싱
    ## YOLO ann 형식으로 변환해서(함수 사용) str 처리하여 만들어 둔 txt 파일에 한 줄씩 작성

    ann_cnt = 0

    with open(jsonfile, 'r') as j:
        data = json.load(j)

        imgs = data.get('images')
        anns = data.get('annotations')

    # img_size = (int(imgs.get('width')), int(imgs.get('height'))) #수정해야됨
    img_size = (1920, 1080)

    ## 경로 제외 파일 이름 파싱, dst 절대경로로 txt 파일 생성
    for idx in range(len(imgs)):
        fname = imgs[idx].get('file_name')
        fname = fname[:-4]
        txt_name = dst + '/' + fname + '.txt'

        txt = open(txt_name, 'w')
        txt.close

        ann_cnt += 1


    for idx in range(len(anns)):
        image_id = int(anns[idx].get('image_id'))
        fname = dst + '/' + imgs[image_id].get('file_name')[:-4] + '.txt'

        ## 내용 - class id
        class_id = str(anns[idx].get('category_id')-1)

        ## 내용 - bbox 좌표
        bbox = anns[idx].get('bbox')    #coco형식: xmin, ymin, w, h
        xmin = float(bbox[0])
        ymin = float(bbox[1])
        w = float(bbox[2])
        h = float(bbox[3])
        bbox_line = convert_coco_to_YOLO(img_size, xmin, ymin, w, h)

        line = class_id + ' ' + bbox_line + '\n'
        
        with open(fname, 'a') as f:
            f.write(line)


    print('{} files converted to [{}]'.format(ann_cnt, dst))
        

## 220113
## json 파일이 여러 개 있는 경로에서 한꺼번에 txt파일로 파싱
def parse_from_multiple_jsonFiles():
    #json 파일이 있는 경로를 받아 해당 경로 내 모든 json파일명을 리스트로 받음 
    #for문으로 하나씩 열어서 변환 실행, 한 폴더에 몰아넣기

    dst_txt = input('txt파일 생성될 root 경로 입력: ')
    dir_json = input('json파일이 있는 경로 입력: ')
    json_list = glob.glob(dir_json+'/*.json')

    for json in json_list:
        convert_json_to_txt(json, dst_txt)

    print('total {} txt files in [{}]'.format(len(glob.glob(dst_txt+'/*.txt')), dst_txt))
    
## 220113
## 이미지가 여러 하위 폴더에 나뉘어져 있는 상위 경로를 입력받아 특정 폴더로 모두 옮김
def move_images_into_one_folder(img_root, img_dst):

    for dirs in os.walk(img_root):
        # print(dirs[0])  #root의 하위폴더
        jpg_list = glob.glob(dirs[0]+'/*.jpg')

        for i in range(len(jpg_list)):
            try:
                split_filename = jpg_list[i].split('/')[-1]

                old_path = jpg_list[i]
                new_path = os.path.join(img_dst, split_filename)

                # shutil.copy2(old_path, new_path)
                shutil.move(old_path, new_path)

            except Exception as e:
                # print(e)
                pass

    print('{} files combining successed'.format(len(glob.glob(img_dst+'/*.jpg'))))
    ## 상태바로 작업 나타내보기

## 220114
## 학습/평가/테스트 에 사용되는 이미지 절대경로가 쓰인 txt 파일 생성(로컬 환경에서 돌릴 때)
def create_imageList_for_training_local():
    tag = input('tag: ')
    imgDir = input('image dir: ')
    purpose = input('train/val/test: ')

    jpg_list = glob.glob(imgDir+'/*.jpg')

    ## 코드가 실행된 곳에 생성됨
    filename = tag + '_' + purpose + '_list.txt'
    with open(filename, 'w') as f:
        for file in jpg_list:
            f.write(file+'\n')

## 211210
## 학습/평가/테스트 에 사용되는 이미지 절대경로가 쓰인 txt 파일 생성(도커 환경에서 돌릴 때) -> 통합 필요
def create_imageList_for_training_docker():
    tag = input('tag: ')
    imgDir = input('image dir: ')
    purpose = input('train/val/test: ')

    jpg_list = glob.glob(imgDir+'/*.jpg')

    filename = tag + '_' + purpose + '_list.txt'
    with open(filename, 'w') as f:
        for i in range(len(jpg_list)):
            name = jpg_list[i].split('/')[-1]
            line = '/home/1_training/220114_NIA/data/images/' + name + '\n'
            f.write(line)


## 220127
def check_missing_filenum(data_root):
    filelist = glob.glob(data_root+'/*.txt')
    
    lists = []
    numbers_under_10 = []
    numbers_under_100 = []
    numbers_under_1000 = []
    numbers_under_10000 = []
    numbers_under_100000 = []

    string = []

    for file in filelist:
        # print(file, '\n')
        
        file_number = file.split('_')[-1].split('.')[0]
    
        ## 1, 10, 100, 1000 단위로 나눈다.
        if int(file_number)<10:  ## 1~9, 9개
            numbers_under_10.append(file_number)
            pass

        elif int(file_number)<100:  ## 10~99, 90개 
            numbers_under_100.append(file_number)
            numbers_under_100.sort()
            pass

        elif int(file_number)<1000:  ## 100~999 900개
            numbers_under_1000.append(file_number)
            numbers_under_1000.sort()
            pass

        elif int(file_number)<10000:  ## 1000~9999, 9000개
            numbers_under_10000.append(file_number)
            numbers_under_10000.sort()
            pass

        elif int(file_number)<100000: ## 10000~99999 90000개
            numbers_under_100000.append(file_number)
            numbers_under_100000.sort()
            pass


    numbers_under_10.sort()
    lists.append(numbers_under_10)

    numbers_under_100.sort()
    lists.append(numbers_under_100)

    numbers_under_1000.sort()
    lists.append(numbers_under_1000)

    numbers_under_10000.sort()
    lists.append(numbers_under_10000)

    numbers_under_100000.sort()
    lists.append(numbers_under_100000)

    # print(*lists, sep='\n')
    # print(len(lists))

    number_of_files = 0
    buff = 0
    for list in lists:

        for i in range(len(list)):
            current_num = int(list[i])
            previous_num = buff

            if current_num - previous_num > 1:
                if i==0:
                    pass

                else:
                    notification = '{} to {} missing ({} files)'.format(previous_num+1, current_num-1, current_num-previous_num-1)
                    string.append(notification)

            elif current_num - previous_num == 1:
                pass

            else:
                print('something wrong -> {}, {}'.format(current_num, previous_num))
            buff = current_num
    
        number_of_files = number_of_files + len(list)

    # print(string)
    # print(len(string))

    if len(string)>0:
        print(*string, sep='\n')

    else:
        print('No missing files')

    jpg_list = glob.glob(data_root+'/*.jpg')
    print('\nTotal labels are {} (last number: {})'.format(len(filelist), current_num))
    print('Total images are {}'.format(len(jpg_list)))

if __name__=='__main__':
    ju = 'yeong'
    ## 경로 입력받을 것.. 등 추가 필요
