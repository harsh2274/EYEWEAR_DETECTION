#Pretrained facial detector module 
import dlib

import cv2
import numpy as np

def landmarks_to_np(landmarks, dtype="int"):
    #collecting the number of fatial marks
    num = landmarks.num_parts
    
    # initializing a list with num rows and 2 colums ,
    # all the points are 0 at first
    coords = np.zeros((num, 2), dtype=dtype)
    
    # loop over the 68 facial landmarks and convert them
    # to a 2-tuple of (x, y)-coordinates
    for i in range(0, num):
        coords[i] = (landmarks.part(i).x, landmarks.part(i).y)

    # return the list of (x, y)-coordinates of face
    return coords


def get_centers(img, landmarks):
    #considering 4 variables out of 68 for eyewear detection
    EYE_LEFT_OUTTER = landmarks[2]
    EYE_LEFT_INNER = landmarks[3]
    EYE_RIGHT_OUTTER = landmarks[0]
    EYE_RIGHT_INNER = landmarks[1]

    #storing of all x values in x
    x = ((landmarks[0:4]).T)[0]
    #storing of all y values in y
    y = ((landmarks[0:4]).T)[1]

    #used to stack arrays vertically
    A = np.vstack([x, np.ones(len(x))]).T
    
    #gives least-squares solution to a linear matrix equation.
    k, b = np.linalg.lstsq(A, y, rcond=None)[0]
    
    #averaging the left eye value
    x_left = (EYE_LEFT_OUTTER[0]+EYE_LEFT_INNER[0])/2
    
    #averaging the right eye value
    x_right = (EYE_RIGHT_OUTTER[0]+EYE_RIGHT_INNER[0])/2

    #taking the centres of bothe the eyes in an array format
    LEFT_EYE_CENTER =  np.array([np.int32(x_left), np.int32(x_left*k+b)])
    RIGHT_EYE_CENTER =  np.array([np.int32(x_right), np.int32(x_right*k+b)])
    
    #will stack bothe the arrays vertically
    pts = np.vstack((LEFT_EYE_CENTER,RIGHT_EYE_CENTER))

    #Drawing of points and lines
    cv2.polylines(img, [pts], False, (255,0,0), 1) 
    cv2.circle(img, (LEFT_EYE_CENTER[0],LEFT_EYE_CENTER[1]), 3, (0, 0, 255), -1)
    cv2.circle(img, (RIGHT_EYE_CENTER[0],RIGHT_EYE_CENTER[1]), 3, (0, 0, 255), -1)
    
    #returning the values
    return LEFT_EYE_CENTER, RIGHT_EYE_CENTER

#checks for the allighnment of face image captured
def get_aligned_face(img, left, right):
    desired_w = 256
    desired_h = 256
    desired_dist = desired_w * 0.5
    
    eyescenter = ((left[0]+right[0])*0.5 , (left[1]+right[1])*0.5)
    dx = right[0] - left[0]
    dy = right[1] - left[1]
    
    #checking of elivation distance
    dist = np.sqrt(dx*dx + dy*dy)

    scale = desired_dist / dist
    angle = np.degrees(np.arctan2(dy,dx))
    
    #rotating the face by the desired angle 
    M = cv2.getRotationMatrix2D(eyescenter,angle,scale)

    # update the translation component of the matrix
    tX = desired_w * 0.5
    tY = desired_h * 0.5
    M[0, 2] += (tX - eyescenter[0])
    M[1, 2] += (tY - eyescenter[1])

    #allighning of the face
    aligned_face = cv2.warpAffine(img,M,(desired_w,desired_h))
    
    return aligned_face
 
#program for judging the presence of an eyeglass  
def judge_eyeglass(img):
    
    #to make the image smooth(helps reducing noise in the image)
    img = cv2.GaussianBlur(img, (11,11), 0) 

    #
    sobel_y = cv2.Sobel(img, cv2.CV_64F, 0 ,1 , ksize=-1) 
    sobel_y = cv2.convertScaleAbs(sobel_y) 
    cv2.imshow('sobel_y',sobel_y)

    edgeness = sobel_y 
    
    retVal,thresh = cv2.threshold(edgeness,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    
    d = len(thresh) * 0.5
    x = np.int32(d * 6/7)
    y = np.int32(d * 3/4)
    w = np.int32(d * 2/7)
    h = np.int32(d * 2/4)

    x_2_1 = np.int32(d * 1/4)
    x_2_2 = np.int32(d * 5/4)
    w_2 = np.int32(d * 1/2)
    y_2 = np.int32(d * 8/7)
    h_2 = np.int32(d * 1/2)
    
    roi_1 = thresh[y:y+h, x:x+w] 
    roi_2_1 = thresh[y_2:y_2+h_2, x_2_1:x_2_1+w_2]
    roi_2_2 = thresh[y_2:y_2+h_2, x_2_2:x_2_2+w_2]
    roi_2 = np.hstack([roi_2_1,roi_2_2])
    
    measure_1 = sum(sum(roi_1/255)) / (np.shape(roi_1)[0] * np.shape(roi_1)[1])
    measure_2 = sum(sum(roi_2/255)) / (np.shape(roi_2)[0] * np.shape(roi_2)[1])
    measure = measure_1*0.3 + measure_2*0.7
    
    cv2.imshow('roi_1',roi_1)
    cv2.imshow('roi_2',roi_2)
    print(measure)
    
    if measure > 0.15:
        judge = True
    else:
        judge = False
    print(judge)
    return judge


predictor_path = r"D:/Eye_Wear_Detection/shape_predictor_5_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)

cap = cv2.VideoCapture(0)

while(cap.isOpened()):
    _, img = cap.read()
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    rects = detector(gray, 1)
    
    for i, rect in enumerate(rects):
        x_face = rect.left()
        y_face = rect.top()
        w_face = rect.right() - x_face
        h_face = rect.bottom() - y_face
        
        cv2.rectangle(img, (x_face,y_face), (x_face+w_face,y_face+h_face), (0,255,0), 2)
        cv2.putText(img, "Face #{}".format(i + 1), (x_face - 10, y_face - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                
        landmarks = predictor(gray, rect)
        landmarks = landmarks_to_np(landmarks)
        for (x, y) in landmarks:
            cv2.circle(img, (x, y), 2, (0, 0, 255), -1)

        LEFT_EYE_CENTER, RIGHT_EYE_CENTER = get_centers(img, landmarks)
        
        aligned_face = get_aligned_face(gray, LEFT_EYE_CENTER, RIGHT_EYE_CENTER)
        cv2.imshow("aligned_face #{}".format(i + 1), aligned_face)
        
        judge = judge_eyeglass(aligned_face)
        if judge == True:
            cv2.putText(img, "With Glasses", (x_face + 100, y_face - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
        else:
            cv2.putText(img, "No Glasses", (x_face + 100, y_face - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
    
    cv2.imshow("Result", img)
    
    k = cv2.waitKey(5) & 0xFF
    if k==27:  
        break

cap.release()
cv2.destroyAllWindows()