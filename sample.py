import cv2

# Replace 'username' and 'password' with your camera's login credentials
username = 'admin'
password = 'Admin@2023'
rtsp_url = 'rtsp://192.168.1.12/live/ch00_1'

# Create an OpenCV VideoCapture object using ffmpeg
cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("Error: Couldn't open the camera feed.")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Display the frame in a window
        cv2.imshow('Live Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the VideoCapture and close the window
    cap.release()
    cv2.destroyAllWindows()
