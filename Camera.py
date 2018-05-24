from picamera import PiCamera
from picamera.array import PiRGBArray
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages')
import RPi.GPIO as GPIO
import time
import numpy
import readchar
import datetime
import cv2
from subprocess import call
class Camera:
    def __init__(self):
        self.camera = PiCamera()
        self.camera.ISO = 100
        self.camera.vflip=True
        self.camera.resolution = (1024, 768)
        self.rawCapture = PiRGBArray(self.camera)
    
    def camClick(self):
        """
            Captures an image
        """
        self.camera.vflip = True
        self.camera.capture('/home/pi/Robot Code/AgriculturalRobotAPI/plantcv/guiimage.jpg')
        time.sleep(1)
    def startPreview(self):
        """
            Starts a live preview on the master camera. Positioning on the window is defined by the arguments in this function.
        """
        self.camera.vflip = True
        self.camera.start_preview(fullscreen=False,window=(1300,600,500,500))
    def pipeline(self):
        """
            Performs the Pipeline function in the PlantCV module. The algorithm is based from the PlantCV website:
            http://plantcv.readthedocs.io/en/latest/vis_tutorial/
        """
        d = datetime.datetime.now()
        datestr = d.strftime("%Y%m%d%H%M%S")
        self.camera.capture("/home/pi/Robot Code/AgriculturalRobotAPI/plantcv/pipeline_image_"+datestr+".png")
        image_loc="/home/pi/Robot Code/AgriculturalRobotAPI/plantcv/pipeline_image_"+datestr+".png"
        call(["python", "plantcv/VIS-Pipeline.py", "-i", image_loc, "-o", "/home/pi/Robot Code/AgriculturalRobotAPI/Images/VIS Pipeline Images/", "-D", "'print'"])
    def ndvi(self):
        """
            Performs the NDVI function. The algorithm is based from that created by user gpolder on the Element 14 Pi IoT forums:
            https://www.element14.com/community/community/design-challenges/pi-iot/blog/2016/08/27/pi-iot-plant-health-camera-11-ndvicampy
        """
        warp_mode = cv2.MOTION_TRANSLATION
        #warp_mode = cv2.MOTION_AFFINE
        #warp_mode = cv2.MOTION_HOMOGRAPHY
        # Define 2x3 or 3x3 matrices and initialize the matrix to identity
        if warp_mode == cv2.MOTION_HOMOGRAPHY :
            warp_matrix = numpy.eye(3, 3, dtype=numpy.float32)
        else :
            warp_matrix = numpy.eye(2, 3, dtype=numpy.float32)
        # Specify the number of iterations.
        number_of_iterations = 5000;
        # Specify the threshold of the increment
        # in the correlation coefficient between two iterations
        termination_eps = 1e-10;
        # Define termination criteria
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, number_of_iterations, termination_eps)

        # allow the camera to warmup
        time.sleep(0.1)

        # GPIO Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(18, GPIO.OUT)
        GPIO.output(18, 0)
        self.camera.capture(self.rawCapture, format="bgr")
        noir_image = self.rawCapture.array
        
        # trigger camera on slave and load
        GPIO.output(18, 1)
        time.sleep(5)
        GPIO.output(18, 0)
        time.sleep(1)
        color_image = cv2.imread('/home/pi/pi1iot_share/planthealthcam/slave_image.jpg',cv2.IMREAD_COLOR)

        # extract nir, red green and blue channel
        nir_channel = noir_image[:,:,0]/256.0
        green_channel = noir_image[:,:,1]/256.0
        blue_channel = noir_image[:,:,2]/256.0
        red_channel = color_image[:,:,0]/256.0

        # align the images
        # Run the ECC algorithm. The results are stored in warp_matrix.
        # Find size of image1
        sz = color_image.shape
        (cc, warp_matrix) = cv2.findTransformECC (color_image[:,:,1],noir_image[:,:,1],warp_matrix, warp_mode, criteria)
        if warp_mode == cv2.MOTION_HOMOGRAPHY :
        # Use warpPerspective for Homography
            nir_aligned = cv2.warpPerspective (nir_channel, warp_matrix, (sz[1],sz[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
        else :
        # Use warpAffine for nit_channel, Euclidean and Affine
            nir_aligned = cv2.warpAffine(nir_channel, warp_matrix, (sz[1],sz[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
                                
        # calculate ndvi
        ndvi_image = (nir_aligned - red_channel)/(nir_aligned + red_channel)
        ndvi_image = (ndvi_image+1)/2
        ndvi_image = cv2.convertScaleAbs(ndvi_image*255)
        ndvi_image = cv2.applyColorMap(ndvi_image, cv2.COLORMAP_JET)

        # calculate gndvi_image
        gndvi_image = (nir_channel - green_channel)/(nir_channel + green_channel)
        gndvi_image = (gndvi_image+1)/2
        gndvi_image = cv2.convertScaleAbs(gndvi_image*255)
        gndvi_image = cv2.applyColorMap(gndvi_image, cv2.COLORMAP_JET)

        # calculate bndvi_image
        bndvi_image = (nir_channel - blue_channel)/(nir_channel + blue_channel)
        bndvi_image = (bndvi_image+1)/2
        bndvi_image = cv2.convertScaleAbs(bndvi_image*255)
        bndvi_image = cv2.applyColorMap(bndvi_image, cv2.COLORMAP_JET)
                                        

        # display the image based on key pressed on screen
##        if c == 'o':
##            cv2.imshow("Image", noir_image)
##        elif c == 'c':
##            cv2.imshow("Image", color_image)
##        elif c == 'n':
##            cv2.imshow("Image", ndvi_image)
##        elif c == 'b':
##            cv2.imshow("Image", bndvi_image)
##        elif c == 'g':
##            cv2.imshow("Image", gndvi_image)
                                                                                    
        # wait at most 10 seconds for a keypress
        cv2.waitKey(10000)
            
        # cleanup
        cv2.destroyAllWindows()
        self.rawCapture.truncate(0)
                                                                                    
        # get current date and time to add to the filenames
        d = datetime.datetime.now()
        datestr = d.strftime("%Y%m%d%H%M%S")

        # save all images
        cv2.imwrite("/home/pi/Robot Code/AgriculturalRobotAPI/Images/NoIR/" + datestr + "_noir.jpg",noir_image)
        cv2.imwrite("/home/pi/Robot Code/AgriculturalRobotAPI/Images/Color/" + datestr + "_color.jpg",color_image)
        cv2.imwrite("/home/pi/Robot Code/AgriculturalRobotAPI/Images/NDVI/" + datestr + "_ndvi.jpg",ndvi_image)
        cv2.imwrite("/home/pi/Robot Code/AgriculturalRobotAPI/Images/GNDVI/" + datestr + "_gndvi.jpg",gndvi_image)
        cv2.imwrite("/home/pi/Robot Code/AgriculturalRobotAPI/Images/BNDVI/" + datestr + "_bndvi.jpg",bndvi_image)

        print "NDVI analysis complete"
