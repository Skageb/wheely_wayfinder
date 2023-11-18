import cv2
import cv2.aruco as aruco
from marker_handler import MarkerHandlers
import inspect


def aruco_thread():
    # Initialize the video capture from the first camera device
    cap = cv2.VideoCapture(0)


    # Get the predefined dictionary
    arucoDict = aruco.getPredefinedDictionary(aruco.DICT_5X5_50)

    detector = aruco.ArucoDetector(arucoDict)

    #Load marker handlers:
    mh = MarkerHandlers()
    handlerFunctions = [func for name, func in inspect.getmembers(mh, inspect.ismethod)]
    current_id = 0
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect the markers in the image using the ArucoDetector object
        corners, ids, rejectedImgPoints = detector.detectMarkers(image=gray)

        # Check if markers are detected
        if ids is not None:
            # If markers are detected, overlay their ID and outline them in the frame
            aruco.drawDetectedMarkers(frame, corners, ids)
        #Checks if new id detected and executes corresponding handler function
        if ids is not None:
            id = ids[0][0]
            if id != current_id:
                handlerFunctions[id-1]()  
                current_id = id
        else:
            #Set current_id to 0 current id is removed from frame
            current_id = 0
        # Display the resulting frame
        cv2.imshow('Frame', frame)
        # Break the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything is done, release the capture and destroy windows
    cap.release()
    cv2.destroyAllWindows()
