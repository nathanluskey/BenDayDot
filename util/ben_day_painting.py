from ezdxf.addons import r12writer
import numpy as np
from PIL import Image, ImageDraw

from ben_day_dot import BenDayDot

from typing import Tuple, List

class BenDayPainting():
    def __init__(self, n_clusters: int, colorSpread: int, smallestDotSize: int, dimensions: Tuple[int, int]) -> None:
        self.benDayDots = list()
        self.n_clusters = n_clusters
        self.colorSpread = colorSpread
        self.smallestDotSize = smallestDotSize
        self.dimensions = dimensions
    
    def AddDot(self, center: Tuple[int, int], diameter: int, subArr: np.ndarray) -> None:
        # Make calculations by flattening out and finding the mode row
        uniqueColors, counts = np.unique(subArr.reshape(-1, subArr.shape[2]), return_counts=True, axis=0)
        modeColor = uniqueColors[np.argmax(counts), :]
        newDot = BenDayDot(diameter, center, modeColor)
        self.benDayDots.append(newDot)
    
    def makeImage(self, filename: str) -> None:
        # https://www.blog.pythonlibrary.org/2021/02/23/drawing-shapes-on-images-with-python-and-pillow/
        # Use ImageDraw ellipse
        image = Image.new("RGB", (self.dimensions[1], self.dimensions[0]), "white")
        draw = ImageDraw.Draw(image)

        # Draw a dot for each dot
        for dot in self.benDayDots:
            radius = int(dot.diameter / 2)
            upper_left_x = dot.center[0] - radius
            upper_left_y = dot.center[1] - radius
            lower_right_x = dot.center[0] + radius
            lower_right_y = dot.center[1] + radius
            draw.ellipse( ( (upper_left_x, upper_left_y), (lower_right_x, lower_right_y) ), fill=dot.color)
        image.save(filename)
    
    def makeDXFs(self, filename: str, dxfDimension: List[int], border=25, hangingHoles=True) -> None:
        # https://ezdxf.readthedocs.io/en/stable/addons/r12writer.html#r12writer
        # Get the maximum X and maximum Y
        maxDotX = 0
        maxDotY = 0
        # Seperate the circles into lists of different clusters
        uniqueColorSets = dict()
        for dot in self.benDayDots:
            colorSet = uniqueColorSets.get(dot.color, set())
            colorSet.add(dot)
            uniqueColorSets[dot.color] = colorSet
            radius = dot.diameter/2
            dotX = dot.center[0] + radius
            dotY = dot.center[1] + radius
            if dotX > maxDotX:
                maxDotX = dotX
            if dotY > maxDotY:
                maxDotY = dotY
        
        # Make an empty white layer
        uniqueColorSets[(255, 255, 255)] = set()

        # Scale the image to the DXF Dimensions
        canvasWidth = dxfDimension[0] - 2*border
        scaleX = canvasWidth / maxDotX
        canvasHeight = dxfDimension[1] - 2*border
        scaleY = canvasHeight / maxDotY
        scale = 0
        borderX = border
        borderY = border
        # Set the minimum scale as the scale. 
        # Add more to the border
        if scaleX <= scaleY:
            scale = scaleX
            canvasHeight = scale * maxDotY
            borderY += (dxfDimension[1] - 2*border - canvasHeight) / 2
        else:
            scale = scaleY
            borderX += (dxfDimension[0] - 2*border - canvasWidth) / 2

        # Iterate over each cluster writing the dots to a unique filename
        for colorIndex, (color, colorDotsSet) in enumerate(uniqueColorSets.items()):
            colorFilename = "{}_{}.dxf".format(filename, color)
            with r12writer(colorFilename) as dxf:
                # TODO: for hanging add holes in even number frames
                # put through slots in odd frames
                # Don't put any holes in the white frame (that's the front)
                if color != (255, 255, 255):
                    dxf.add_circle((borderX/2, 2/3 * dxfDimension[1]), radius=border/4)
                    dxf.add_circle((borderX/2, 2/3 * dxfDimension[1] + border), radius=border/4)
                    dxf.add_circle((dxfDimension[0] - borderX/2, 2/3 * dxfDimension[1]), radius=border/4)
                    dxf.add_circle((dxfDimension[0] - borderX/2, 2/3 * dxfDimension[1] + border), radius=border/4)
                    if colorIndex % 2 == 1:
                        dxf.add_line((borderX/2 - border/4, 2/3 * dxfDimension[1]), (borderX/2 - border/4, 2/3 * dxfDimension[1] + border))
                        dxf.add_line((borderX/2 + border/4, 2/3 * dxfDimension[1]), (borderX/2 + border/4, 2/3 * dxfDimension[1] + border))
                        dxf.add_line((dxfDimension[0] - borderX/2 - border/4, 2/3 * dxfDimension[1]), (dxfDimension[0] - borderX/2 - border/4, 2/3 * dxfDimension[1] + border))
                        dxf.add_line((dxfDimension[0] - borderX/2 + border/4, 2/3 * dxfDimension[1]), (dxfDimension[0] - borderX/2 + border/4, 2/3 * dxfDimension[1] + border))
                
                # Draw a rectangle around everything
                dxf.add_line((0,0), (dxfDimension[0],0))
                dxf.add_line((dxfDimension[0],0), (dxfDimension[0],dxfDimension[1]))
                dxf.add_line((dxfDimension[0],dxfDimension[1]),(0,dxfDimension[1]))
                dxf.add_line((0,dxfDimension[1]), (0,0))

                # Draw 4 circles at each corner
                dxf.add_circle((borderX/2, borderY/2), radius=border/4)
                dxf.add_circle((dxfDimension[0] - borderX/2, borderY/2), radius=border/4)
                dxf.add_circle((borderX/2, dxfDimension[1] - borderY/2), radius=border/4)
                dxf.add_circle((dxfDimension[0] - borderX/2, dxfDimension[1] - borderY/2), radius=border/4)
                
                # Draw a circle where the dot *doesn't* exist
                for dot in self.benDayDots:
                    if dot not in colorDotsSet:
                        dotX = dot.center[0]*scale + borderX
                        dotY = (maxDotY - dot.center[1])*scale + borderY
                        dxf.add_circle((dotX, dotY), radius=dot.diameter*scale/2)