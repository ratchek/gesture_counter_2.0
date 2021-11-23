# from
# https://livecodestream.dev/post/detecting-face-features-with-python/
## TODO: Clean up code.
## TODO: Add a nicer interface. Delete blinking black screen
## TODO: For now the detector assumes that your head is such that your eyes are approximately parrallel to the bottom of the frame
## because it only measures the x distance when detecting shakes and the y distance when detecting nods.
## A good update would be to take the cartesian distance instead which should be simple to implement.
## However you'd need to recalibrate everything again and that part would be a pain.

import cv2
import dlib


def get_distances(frame, points_of_interest, detector):
    # Convert image into grayscale
    gray = cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2GRAY)
    # Use detector to find landmarks
    faces = detector(gray)

    for face in faces:
        # Create landmark object
        landmarks = predictor(image=gray, box=face)
        try:
            distance_in_x = abs( landmarks.part(points_of_interest["bridge_of_nose"]).x - landmarks.part(points_of_interest["corner_of_eye"]).x )
            distance_in_y = abs( landmarks.part(points_of_interest["chin"]).y - landmarks.part(points_of_interest["tip_of_nose"]).y )
        except:
            raise
        else:
            return distance_in_x, distance_in_y

    return 0,0

# Load the detector
detector = dlib.get_frontal_face_detector()

# Load the predictor
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# read the image
cap = cv2.VideoCapture(0)
points_of_interest = {
    "chin" : 8,
    "tip_of_nose": 33,
    "corner_of_eye": 36, # outside corner of right eye  (image will be inverted, but that's okself.)
    "bridge_of_nose": 27, # bridge of nose
}


font = cv2.FONT_HERSHEY_SIMPLEX


# We're going to be counting the total sum of changes in distance in the x and y directions from frame to frame between cetain points.
# If for example a head rotates, the absolute distance between the corner of the eye and the bridge of the nose will changes because we're
# projecting a 3d object onto a 2d screen. Once a certain treshold of total change is accumulated, we assume that the head has been rotating.
counter = 0

HORIZONTAL_CHANGE_THRESHOLD = 30
VERTICAL_CHANGE_THRESHOLD = 20
TOTAL_REFRESH_RATE_IN_SECONDS = 0.5 # How often the "total" counter get's reset to zero (used to prevent accumulated mini gestures setting off the gesture detection)
TOTAL_REFRESH_RATE = TOTAL_REFRESH_RATE_IN_SECONDS * cap.get(5) # Number of frames between refreshing the "total" counter
total_refresh_rate = TOTAL_REFRESH_RATE

GESTURE_COOLDOWN_IN_SECONDS = 1 # Number of seconds between detecting gestures. Used to prevent duplicate detection
GESTURE_COOLDOWN = GESTURE_COOLDOWN_IN_SECONDS * cap.get(5)  # Number of frames that a gesture can't be detected after one has been already detected
gesture_cooldown = 0

distance_in_x = 0
distance_in_y = 0
total_horizontal_change = 0
total_vertical_change = 0

print (cap.get(3), cap.get(4), cap.get(5) )

while True:
    _, frame = cap.read()

    # Compute the difference in distances between the markers between frames
    # If the previous frame did not detect a face, you need to gather your whereabouts again before you start computing differences
    if distance_in_x == 0:
        try:
            distance_in_x, distance_in_y = get_distances(frame, points_of_interest, detector)
        except ValueError:
            pass
        cv2.putText(frame, "NO FACE DETECTED",  (100,150), font, 1 , (0, 0, 255) , 3)
    else:
        previous_distance_in_x = distance_in_x
        previous_distance_in_y = distance_in_y
        try:
            distance_in_x, distance_in_y = get_distances(frame, points_of_interest, detector)
        except ValueError:
            distance_in_x = 0
            distance_in_y = 0
        else:
            distance_change_x = abs(previous_distance_in_x - distance_in_x)
            distance_change_y = abs(previous_distance_in_y - distance_in_y)
            print ("x = %d, y = %d"%(distance_change_x, distance_change_y))
            if distance_change_x < 40 and distance_change_x >3:
                total_horizontal_change += distance_change_x
            if distance_change_y < 40 and distance_change_y >3:
                total_vertical_change += distance_change_y


    # If a shake is detected
    if total_horizontal_change > HORIZONTAL_CHANGE_THRESHOLD:
        total_horizontal_change = 0
        total_vertical_change = 0
        if gesture_cooldown <= 0:
            counter = max(0, counter - 1)
            gesture_cooldown = GESTURE_COOLDOWN

    if total_vertical_change > VERTICAL_CHANGE_THRESHOLD:
        total_horizontal_change = 0
        total_vertical_change = 0
        if gesture_cooldown <= 0:
            counter += 1
            gesture_cooldown = GESTURE_COOLDOWN

    gesture_cooldown = max(0, gesture_cooldown - 1)

    total_refresh_rate -= 1
    if total_refresh_rate <= 0:
        total_refresh_rate = TOTAL_REFRESH_RATE
        cv2.rectangle( frame, (0,0),  (640,480),  (0,0,0),  -1)
        total_horizontal_change = 0
        total_vertical_change = 0

    cv2.putText(frame,'Dziesiatki: %d'%(counter//10),(50,150), font, 1.2,(0,0,255),3)
    cv2.putText(frame,'Paciorki: %d'%(counter%10),(50,200), font, 1.2,(0,0,255),3)


    cv2.putText(frame, "Horizontal change = %d"%(total_horizontal_change),  (50,50), font, 0.75 , (0, 255, 0) , 1)
    cv2.putText(frame, "Vertical change = %d"%(total_vertical_change),  (50,100), font, 0.75 , (0, 255, 0) , 1)
    # show the image
    cv2.imshow(winname="Face", mat=frame)

    # Exit when escape is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the video capture and video write objects
cap.release()

# Close all windows
cv2.destroyAllWindows()
