from __future__ import annotations
from typing import Tuple
from os.path import abspath, dirname
from os import listdir
from itertools import combinations
import zipfile

def readManiaOsu(filePath: str, openFunc: function, initialTimingPoint: int = None) -> Tuple[list, int]:
    returnList = []
    hitObjectSectionFound = False
    oldTime = None
    timingOffset = -1
    with openFunc(filePath, "r") as osu_file:
        while True:
            line = osu_file.readline()
            try: line = line.decode() 
            except: pass 
            if not line:
                break
            if not hitObjectSectionFound:
                if line.startswith("[TimingPoints]"):
                    while True:
                        line = osu_file.readline()
                        try: line = line.decode() 
                        except: pass 
                        timestamp,beatLength,_,_,_,_,uninherited,_ = line.split(",", 7)
                        print(f"timestamp: {timestamp}, bpm: {60000 / float(beatLength):.4f}, uninherited: {uninherited}")
                        if uninherited:
                            if initialTimingPoint is not None:
                                timingOffset = initialTimingPoint - float(timestamp)
                            else:
                                timingOffset = float(timestamp)
                            break
                if line.startswith("[HitObjects]"):
                    hitObjectSectionFound = True
            else:
                column,_,time,objectType,_,endTime, = line.split(':')[0].split(',', 6)[0:6]
                if initialTimingPoint is not None:
                    time = int(time) + timingOffset
                    endTime = int(endTime) + timingOffset
                time = int(time)
                endTime = int(endTime)
                column = int(column)
                newObject = (column,) if int(objectType) & 129 != 128 else (column, endTime)
                if time == oldTime:
                    returnList[-1].append(newObject)
                else:
                    returnList.append([time, newObject])
                    oldTime=time
    return (returnList, timingOffset)

print("Put .osu or .osz files you want to compare into this programs Folder")
print("(press enter)")
input()

file_directory = dirname(abspath(__file__))

osuFiles = [(path, open) for path in listdir(file_directory) if path.endswith(".osu") or path.endswith(".osz")]

offset=0
for i in range(len(osuFiles)):
    if not osuFiles[i+offset][0].endswith(".osz"): continue
    #print(f"osz: {filePath}")
    zip = zipfile.ZipFile(osuFiles[i+offset][0])
    oszContent = zip.namelist()
    print(oszContent)
    for fileName in oszContent:
        if fileName.endswith(".osu"):
            osuFiles.append((fileName, zip.open))
    osuFiles.pop(i+offset)
    offset -= 1

fileCombinations = list(combinations(osuFiles, 2))

limit=33*(1/40*len(fileCombinations)/((1/40*len(fileCombinations)+1)))

while fileCombinations:
    print("\n\n")
    list1, timingOffset = readManiaOsu(*fileCombinations[0][0])
    list2,_ = readManiaOsu(*fileCombinations[0][1], timingOffset)
    print("Comparing: \n",fileCombinations[0][0][0],"\n",fileCombinations[0][1][0])
    fileCombinations.pop(0)

    if list1[-1][0] > list2[-1][0]:
        list1_ = list1
        list1 = list2
        list2 = list1_

    for timestamp in list1:
        timestamp[1:] = sorted(timestamp[1:], key=lambda hitObject: hitObject[0])
    for timestamp in list2:
        timestamp[1:] = sorted(timestamp[1:], key=lambda hitObject: hitObject[0])

    a=0
    i=0
    same=0
    differentLN=0
    while a < len(list1):
        if abs(list1[a][0] - list2[i][0]) <=2:
            if len(list1[a]) == len(list2[i]):
                if list1[a][1:] == list2[i][1:]:
                    same+=1
                else:
                    first = [hitObject[0] for hitObject in list1[a][1:]]
                    second = [hitObject[0] for hitObject in list2[i][1:]]
                    if first == second:
                        differentLN+=1
        if int(list1[a][0]) <= int(list2[i][0]):
            i-=1
        else:
            a-=1
        a -=- 1
        i -=- 1
    if  (same+(differentLN/2))/len(list2)*100 >= limit:
        print("Total Chords: ",max(len(list1),len(list2)),"\nSame Chords: ",same,"\nSame, but LN different: ",differentLN,f"\nSimilarity: {((same+(differentLN/2))/max(len(list1),len(list2))*100):.48f}%")
        print("**DISCLAIMER: Does not include mirrored or otherwise slightly altered patterns")
        input("continue ->")
