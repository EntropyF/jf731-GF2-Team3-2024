"""Implement the graphical user interface for the Logic Simulator.

Used in the Logic Simulator project to enable the user to run the simulation
or adjust the network properties.

Classes:
--------
MyGLCanvas - handles all canvas drawing operations.
Gui - configures the main window and all the widgets.
"""
import wx
import wx.glcanvas as wxcanvas
from OpenGL import GL, GLUT, GLU
import numpy as np
import math
import os

from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser


class MyGLCanvas(wxcanvas.GLCanvas):
    """Handle all drawing operations.

    This class contains functions for drawing onto the canvas. It
    also contains handlers for events relating to the canvas.

    Parameters
    ----------
    parent: parent window.
    devices: instance of the devices.Devices() class.
    monitors: instance of the monitors.Monitors() class.

    Public methods
    --------------
    init_gl(self): Configures the OpenGL context.

    render_graph_axes(self, x, y): Draw axis for a given signal output.

    render_trace(self, x, y, values, name): Draw a signal output trace.

    render(self, text): Handles all drawing operations.

    on_paint(self, event): Handles the paint event.

    on_size(self, event): Handles the canvas resize event.

    on_mouse(self, event): Handles mouse events.

    render_text(self, text, x_pos, y_pos): Handles text drawing
                                           operations.
    """

    def __init__(self, parent, devices, monitors):
        """Initialise canvas properties and useful variables."""
        super().__init__(parent, -1,
                         attribList=[wxcanvas.WX_GL_RGBA,
                                     wxcanvas.WX_GL_DOUBLEBUFFER,
                                     wxcanvas.WX_GL_DEPTH_SIZE, 16, 0])
        GLUT.glutInit()
        self.init = False
        self.reset_3D = False
        self.context = wxcanvas.GLContext(self)

        # Gain access to Gui Class parent's variables
        self.parent = parent

        # Initialise store for monitors and devices
        self.monitors = monitors
        self.devices = devices
        self.oscillating = False
        self.not_connected = False

        # two different canvas for 2D and 3D
        self.screen_type = (1, 0)

        # 3D Parameters
        self.clear_color = (0.0, 0.0, 0.0, 0.0)

        # Constants for OpenGL materials and lights
        self.mat_diffuse = [0.0, 0.0, 0.0, 1.0]
        self.mat_no_specular = [0.0, 0.0, 0.0, 0.0]
        self.mat_no_shininess = [0.0]
        self.mat_specular = [0.5, 0.5, 0.5, 1.0]
        self.mat_shininess = [50.0]
        self.top_right = [1.0, 1.0, 1.0, 0.0]
        self.straight_on = [0.0, 0.0, 1.0, 0.0]
        self.no_ambient = [0.0, 0.0, 0.0, 1.0]
        self.dim_diffuse = [0.5, 0.5, 0.5, 1.0]
        self.bright_diffuse = [1.0, 1.0, 1.0, 1.0]
        self.med_diffuse = [0.75, 0.75, 0.75, 1.0]
        self.full_specular = [0.5, 0.5, 0.5, 1.0]
        self.no_specular = [0.0, 0.0, 0.0, 1.0]

        # Initialise the scene rotation matrix
        self.scene_rotate = np.identity(4, 'f')

        # Offset between viewpoint and origin of the scene
        self.depth_offset = 400

        # Initialise variables for panning
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0  # previous mouse x position
        self.last_mouse_y = 0  # previous mouse y position

        # Initialise variables for zooming
        self.zoom = 1

        # Bind events to the canvas
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)

    def init_gl(self):
        """Configure and initialise the OpenGL context."""
        size = self.GetClientSize()
        self.SetCurrent(self.context)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glClearColor(1.0, 1.0, 1.0, 0.0)
        GL.glViewport(0, 0, size.width, size.height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, size.width, 0, size.height, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glTranslated(self.pan_x, self.pan_y, 0.0)
        GL.glScaled(self.zoom, self.zoom, self.zoom)

    def init_gl_3D(self):
        """Configure and initialise the OpenGL context."""
        size = self.GetClientSize()
        self.SetCurrent(self.context)

        GL.glViewport(0, 0, size.width, size.height)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GLU.gluPerspective(45, size.width / size.height, 10, 10000)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()  # lights positioned relative to the viewer
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, self.no_ambient)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, self.med_diffuse)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, self.no_specular)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, self.top_right)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_AMBIENT, self.no_ambient)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_DIFFUSE, self.dim_diffuse)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_SPECULAR, self.no_specular)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_POSITION, self.straight_on)

        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, self.mat_specular)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SHININESS, self.mat_shininess)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE,
                        self.mat_diffuse)
        GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)

        GL.glClearColor(*self.clear_color)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glCullFace(GL.GL_BACK)
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        GL.glEnable(GL.GL_LIGHT1)
        GL.glEnable(GL.GL_NORMALIZE)

        # Viewing transformation - set the viewpoint back from the scene
        GL.glTranslatef(0.0, 0.0, -self.depth_offset)

        # Modelling transformation - pan, zoom and rotate
        GL.glTranslatef(self.pan_x, self.pan_y, 0.0)
        GL.glMultMatrixf(self.scene_rotate)
        GL.glScalef(self.zoom, self.zoom, self.zoom)

    def render_graph_axes(self, x, y):
        """Draw axis for a given signal output."""
        time_step_no = len(self.parent.values[0])
        GL.glColor3f(0.0, 0.0, 0.8)  # axis is blue

        GL.glBegin(GL.GL_LINE_STRIP)
        GL.glVertex2f(x - 4, y + 29)
        GL.glVertex2f(x - 4, y - 4)
        GL.glVertex2f(x + 4 + (time_step_no * 20), y - 4)
        GL.glEnd()
        GL.glFlush()

        if self.zoom > 0.8:
            for i in range(time_step_no + 1):
                self.render_text(str(i), x - 4 + (20 * i), y - 16)
        elif self.zoom > 0.5:
            for i in range(time_step_no + 1):
                if i % 5 == 0:
                    self.render_text(str(i), x - 4 + (20 * i), y - 16)
        else:
            for i in range(time_step_no + 1):
                if i % 10 == 0:
                    self.render_text(str(i), x - 4 + (20 * i), y - 16)

        self.render_text('0', x - 14, y - 6)
        self.render_text('1', x - 14, y + 19)

    def render_trace(self, x, y, values, name):
        """Draw a signal output trace."""
        self.render_text(name, 10, y + 5)  # name is signal name
        GL.glColor3f(0.8, 0.4, 0.2)  # trace is Red
        GL.glBegin(GL.GL_LINE_STRIP)
        for i in range(len(values)):  # values is a list of 0/1
            j = i + self.parent.time_steps - len(values)
            x0 = (j * 20) + x
            x1 = (j * 20) + x + 20
            if values[i]:  # if values[i] is 1, signal raising
                y0 = y + 25
            else:
                y0 = y

            GL.glVertex2f(x0, y0)
            GL.glVertex2f(x1, y0)
        GL.glEnd()
        GL.glFlush()

    def render_2D(self, text):
        """Handle all drawing operations."""
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        self.canvas_size = self.GetClientSize()

        # # Test trace_names and values
        # self.parent.trace_names = ["A1", "N1"]
        # self.parent.values = [[1,0,1,0,1,0,1,0,1,0], [1,1,0,0,1,1,0,0,1,1]]

        if not self.parent.values:
            self.parent.trace_names = ['Click Run to START']
            self.parent.values = [[]]

        display_ys = [self.canvas_size[1] - 100 - 80 * j for j in
                      range(len(self.parent.values))]
        display_x = 120
        signal_no = len(self.parent.trace_names)

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        # Draw specified text at position (10, 10)
        # self.render_text(text, 10, 10)
        # self.render_text(text, 10, self.canvas_size[1] - 40)

        # Draw title
        title_text = ("Monitored Signal Display")
        self.render_text(title_text, 10, self.canvas_size[1] - 20, title=True)

        if self.not_connected:
            self.render_text('Not all input connected...', 10,
                             self.canvas_size[1] - 60)

        elif self.oscillating:
            self.render_text('Network Oscillating...', 10,
                             self.canvas_size[1] - 60)

        elif self.parent.trace_names == ['Click Run to START']:
            self.render_text('Click Run button to START.', 10,
                             self.canvas_size[1] - 60, title=True)
        else:
            for j in range(signal_no):
                self.render_trace(display_x, display_ys[j],
                                  self.parent.values[j],
                                  self.parent.trace_names[j])
                self.render_graph_axes(display_x, display_ys[j])

        # We have been drawing to the back buffer, flush the graphics pipeline
        # and swap the back buffer to the front
        GL.glFlush()
        self.SwapBuffers()

    def render(self, text):
        """Decide which screen type to render and render the canvas."""
        if self.screen_type[1]:
            self.render_3D()
        else:
            self.render_2D(text)

    def on_paint(self, event):
        """Handle the paint event."""
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        size = self.GetClientSize()
        text = "".join(["Canvas redrawn on paint event, size is ",
                        str(size.width), ", ", str(size.height)])
        self.render(text)

    def on_size(self, event):
        """Handle the canvas resize event."""
        # Forces reconfiguration of the viewport, modelview and projection
        # matrices on the next paint event
        self.init = False

    def on_mouse(self, event):
        """Handle mouse events."""
        text = ""
        # Calculate object coordinates of the mouse position
        size = self.GetClientSize()
        ox = (event.GetX() - self.pan_x) / self.zoom
        oy = (size.height - event.GetY() - self.pan_y) / self.zoom
        old_zoom = self.zoom
        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            text = "".join(["Mouse button pressed at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.ButtonUp():
            text = "".join(["Mouse button released at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.Leaving():
            text = "".join(["Mouse left canvas at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.Dragging():
            if self.screen_type[1]:
                GL.glMatrixMode(GL.GL_MODELVIEW)
                GL.glLoadIdentity()
                x = event.GetX() - self.last_mouse_x
                y = event.GetY() - self.last_mouse_y
                if event.LeftIsDown():
                    GL.glRotatef(math.sqrt((x * x) + (y * y)), y, x, 0)
                if event.MiddleIsDown():
                    GL.glRotatef((x + y), 0, 0, 1)
                if event.RightIsDown():
                    self.pan_x += x
                    self.pan_y -= y
                GL.glMultMatrixf(self.scene_rotate)
                GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX, self.scene_rotate)
                self.last_mouse_x = event.GetX()
                self.last_mouse_y = event.GetY()
                self.init = False
                text = "test"
                # print(self.scene_rotate)
            else:
                self.pan_x += event.GetX() - self.last_mouse_x
                self.pan_y -= event.GetY() - self.last_mouse_y
                self.last_mouse_x = event.GetX()
                self.last_mouse_y = event.GetY()
                self.init = False
                text = "".join(["Mouse dragged to: ", str(event.GetX()),
                                ", ", str(event.GetY()), ". Pan is now: ",
                                str(self.pan_x), ", ", str(self.pan_y)])
        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            # Adjust pan so as to zoom around the mouse position
            self.pan_x -= (self.zoom - old_zoom) * ox
            self.pan_y -= (self.zoom - old_zoom) * oy
            self.init = False
            text = "".join(["Negative mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])
        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            # Adjust pan so as to zoom around the mouse position
            self.pan_x -= (self.zoom - old_zoom) * ox
            self.pan_y -= (self.zoom - old_zoom) * oy
            self.init = False
            text = "".join(["Positive mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])
        if text:
            self.render(text)
        else:
            self.Refresh()  # triggers the paint event

    def render_text(self, text, x_pos, y_pos, title=False):
        """Handle text drawing operations."""
        # Add additional attribute of title or not
        GL.glColor3f(0.0, 0.0, 0.0)  # text is black
        GL.glRasterPos2f(x_pos, y_pos)

        if not title:
            font = GLUT.GLUT_BITMAP_HELVETICA_12
        else:
            font = GLUT.GLUT_BITMAP_HELVETICA_18

        for character in text:
            if character == '\n':
                y_pos = y_pos - 20
                GL.glRasterPos2f(x_pos, y_pos)
            else:
                GLUT.glutBitmapCharacter(font, ord(character))

    def render_3D(self):
        """Handle all drawing operations."""
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the OpenGL rendering context
            self.init_gl_3D()
            self.init = True

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Draw a sample signal trace, make sure its centre of gravity
        # is at the scene origin
        # self.parent.time_steps = 10
        # self.render_trace_3D(0, 0, [0, 1, 1, 1, 0, 1, 1, 0, 0, 1], "test")
        # self.render_trace_3D(0, 50, [1, 0, 0, 0, 1, 0, 1, 0, 0, 1], "test2")

        if not self.parent.values:
            self.parent.trace_names = ['Click Run to START']
            self.parent.values = [[]]

        axes_spacing = max(50, 50 / self.zoom)

        display_ys = [(j - len(self.parent.values)/2) * axes_spacing
                      for j in range(len(self.parent.values))]

        # Draw title
        title_text = ("Monitored Signal Display")
        self.render_text(title_text, 10, self.canvas_size[1] - 20, title=True)

        if self.not_connected:
            self.render_text('Not all input connected...', 10,
                             self.canvas_size[1] - 60)

        elif self.oscillating:
            self.render_text('Network Oscillating...', 10,
                             self.canvas_size[1] - 60)

        elif self.parent.trace_names == ['Click Run to START']:
            self.render_text('Click Run button to START.', 10,
                             self.canvas_size[1] - 60, title=True)
        else:
            for j, name in enumerate(self.parent.trace_names):
                self.render_trace_3D(0, display_ys[j], self.parent.values[j],
                                     name)

        # We have been drawing to the back buffer, flush the graphics pipeline
        # and swap the back buffer to the front
        GL.glFlush()
        self.SwapBuffers()

    def render_trace_3D(self, x, y, values, name):
        GL.glColor3f(0.8, 0.4, 0.2)  # signal trace is orange
        width = 20
        depth = 4
        axes_depth = 8
        axes_height = 20

        for i in range(len(values)):
            j = i + self.parent.time_steps/2 - len(values)
            x0 = j * width + x
            if values[i]:
                height = 11
            else:
                height = 1

            self.draw_cuboid(x0, y, 0, width/2, depth/2, height)

        # Axes
        GL.glColor3f(0.4, 0.4, 0.4)
        axes_x = (-self.parent.time_steps/2 - 0.5) * width
        axes_y = y - 2
        self.draw_cuboid(axes_x-1, axes_y, 0, 1, axes_depth/2, axes_height)

        self.draw_cuboid(0, axes_y, 0, -axes_x, axes_depth/2, 2)

        # Title label
        text_x = (-self.parent.time_steps/2 - 0.5) * width
        GL.glColor3f(1.0, 1.0, 1.0)  # text is white
        self.render_text_3D(name, text_x, y + axes_height, 0)

        # Axes labes
        GL.glColor3f(0.5, 0.5, 1.0)  # axis is blue
        if self.zoom < 0.1:
            step = 10
        elif self.zoom < 0.8:
            step = 5
        else:
            step = 1

        for i in range(0, self.parent.time_steps, step):
            x = (i - self.parent.time_steps/2 - 0.5) * 20
            self.render_text_3D(str(i), x, y - 10, 0)

    def render_text_3D(self, text, x_pos, y_pos, z_pos):
        """Handle text drawing operations."""
        GL.glDisable(GL.GL_LIGHTING)
        GL.glRasterPos3f(x_pos, y_pos, z_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_10

        for character in text:
            if character == '\n':
                y_pos = y_pos - 20
                GL.glRasterPos3f(x_pos, y_pos, z_pos)
            else:
                GLUT.glutBitmapCharacter(font, ord(character))

        GL.glEnable(GL.GL_LIGHTING)

    def draw_cuboid(self, x_pos, y_pos, z_pos, half_width, half_depth, height):
        """Draw a cuboid.

        Draw a cuboid at the specified position, with the specified
        dimensions.
        """
        GL.glBegin(GL.GL_QUADS)
        GL.glNormal3f(0, -1, 0)
        GL.glVertex3f(x_pos - half_width, y_pos, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos, z_pos + half_depth)
        GL.glNormal3f(0, 1, 0)
        GL.glVertex3f(x_pos + half_width, y_pos + height, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos + height, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos + height, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos + height, z_pos + half_depth)
        GL.glNormal3f(-1, 0, 0)
        GL.glVertex3f(x_pos - half_width, y_pos + height, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos + height, z_pos + half_depth)
        GL.glNormal3f(1, 0, 0)
        GL.glVertex3f(x_pos + half_width, y_pos, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos + height, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos + height, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos, z_pos + half_depth)
        GL.glNormal3f(0, 0, -1)
        GL.glVertex3f(x_pos - half_width, y_pos, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos + height, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos + height, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos, z_pos - half_depth)
        GL.glNormal3f(0, 0, 1)
        GL.glVertex3f(x_pos - half_width, y_pos + height, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, y_pos, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, y_pos + height, z_pos + half_depth)
        GL.glEnd()


class Gui(wx.Frame):
    """Configure the main window and all the widgets.

    This class provides a graphical user interface for the Logic Simulator and
    enables the user to change the circuit properties and run simulations.

    Parameters
    ----------
    title: title of the window.

    Public methods
    --------------
    Toolbarhandler(self, event): Handles toolbar presses.

    on_spin(self, event): Event handler for when the user changes the spin
                           control value.

    on_run_button(self, event): Event handler for when the user clicks the run
                                button.

    on_continue_button(self, event): Event handler for when the user clicks the
                                        continue button.

    run_network_and_get_values(self): Run the network and get the monitored
                                        signal values.

    on_text_box(self, event): Event handler for when the user enters text.
                                (Functions TBC)

    on_switch_choice(self, event): Handle the new_switch_choice event.

    on_switch_set(self, event): Handle the switch_set event.

    on_add_monitor_button(self, event): User add monitors using this button.

    on_remove_monitor_button(self, event): User can remove monitors using this
                                            button.
    """

    def __init__(self, title, path, names, devices, network, monitors):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title=title, size=(800, 600))
        self.QuitID = 999
        self.OpenID = 998
        self.AboutID = 997
        self.HelpID = 996
        # self.HomeID = 995
        self.CubeID = 994

        # Store for monitored signal from network
        self.values = None
        self.trace_names = None
        self.time_steps = 1

        # Store inputs from logsim.py
        self.title = title
        self.path = path
        self.names = names
        self.devices = devices
        self.network = network
        self.monitors = monitors

        # Setup switch information and signal names under
        # and not under monitored
        self.switch_ids = self.devices.find_devices(self.devices.SWITCH)

        if self.switch_ids:
            self.switch_names = [self.names.get_name_string(i) for i in
                                 self.switch_ids]
            self.switch_values = [self.devices.get_switch_value(i) for i in
                                  self.switch_ids]

        self.sig_mons, self.sig_not_mons = self.monitors.get_signal_names()

        # Setup the toolbar
        toolbar = self.CreateToolBar()
        # myimage = wx.ArtProvider.GetBitmap(wx.ART_GO_HOME, wx.ART_TOOLBAR)
        # toolbar.AddTool(self.HomeID, "Home", myimage)
        myimage = wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_TOOLBAR)
        toolbar.AddTool(self.CubeID, "Toggle view", myimage)
        myimage = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR)
        toolbar.AddTool(self.OpenID, "Open file", myimage)
        myimage = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_TOOLBAR)
        toolbar.AddTool(self.AboutID, "About", myimage)
        myimage = wx.ArtProvider.GetBitmap(wx.ART_HELP, wx.ART_TOOLBAR)
        toolbar.AddTool(self.HelpID, "Help", myimage)
        myimage = wx.ArtProvider.GetBitmap(wx.ART_QUIT, wx.ART_TOOLBAR)
        toolbar.AddTool(self.QuitID, "Quit", myimage)
        toolbar.Bind(wx.EVT_TOOL, self.Toolbarhandler)
        toolbar.Realize()
        self.ToolBar = toolbar

        # Canvas for drawing signals
        self.canvas = MyGLCanvas(self, devices, monitors)

        # Configure the widgets
        self.text = wx.StaticText(self, wx.ID_ANY, _("Cycles:"))
        self.spin = wx.SpinCtrl(self, wx.ID_ANY, "10")
        self.run_button = wx.Button(self, wx.ID_ANY, _("Run"))
        self.continue_button = wx.Button(self, wx.ID_ANY, _("Continue"))

        # # Test setting for temporary use
        # self.switch_ids = [0, 1, 2]
        # self.switch_names = ['S1', 'S2', 'S3']
        # self.switch_values = [1, 0, 1]
        # self.sig_not_mons = ['A1', 'N1']
        # self.sig_mons = ['G1', 'D1']

        # Switch widgets
        if self.switch_ids:
            self.text_switch_control = wx.StaticText(self, wx.ID_ANY,
                                                     _("Switch State: "))
            self.switch_choice = wx.ComboBox(self, wx.ID_ANY, "<SWITCH>",
                                             choices=self.switch_names,
                                             style=wx.CB_READONLY)

            self.switch_choice.SetValue(self.switch_names[0])
            self.switch_set = wx.CheckBox(self, wx.ID_ANY)

        # Monitor Add/Remove widgets
        self.text_monitor = wx.StaticText(self, wx.ID_ANY,
                                          _("Monitor Control:"))
        self.add_monitor_button = wx.Button(self, wx.ID_ANY, _("Add"))
        self.remove_monitor_button = wx.Button(self, wx.ID_ANY, _("Remove"))
        self.add_monitor_choice = wx.ComboBox(self, wx.ID_ANY, "",
                                              choices=self.sig_not_mons,
                                              style=wx.CB_READONLY)
        self.remove_monitor_choice = wx.ComboBox(self, wx.ID_ANY, "",
                                                 choices=self.sig_mons,
                                                 style=wx.CB_READONLY)
        if len(self.sig_not_mons):  # if sig_not_mons list is not empty
            self.add_monitor_choice.SetValue(self.sig_not_mons[0])
        if len(self.sig_mons):
            self.remove_monitor_choice.SetValue(self.sig_mons[0])

        # Bind events to widgets
        self.spin.Bind(wx.EVT_SPINCTRL, self.on_spin)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_button)
        self.continue_button.Bind(wx.EVT_BUTTON, self.on_continue_button)
        # self.text_box.Bind(wx.EVT_TEXT_ENTER, self.on_text_box)

        if self.switch_ids:
            self.switch_choice.Bind(wx.EVT_COMBOBOX, self.on_switch_choice)
            self.switch_set.Bind(wx.EVT_CHECKBOX, self.on_switch_set)
        self.add_monitor_button.Bind(wx.EVT_BUTTON, self.on_add_monitor_button)
        self.remove_monitor_button.Bind(wx.EVT_BUTTON,
                                        self.on_remove_monitor_button)

        # Configure sizers for layout
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        side_sizer = wx.BoxSizer(wx.VERTICAL)
        # Contain run and continue buttons
        side_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        # Contain Switch droplist and checkbox
        side_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        # Add Monitor line
        side_sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        # Remove Monitor line
        side_sizer4 = wx.BoxSizer(wx.HORIZONTAL)

        main_sizer.Add(self.canvas, 5, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(side_sizer, 1, wx.ALL, 5)

        # Cycle and spin
        side_sizer.Add(self.text, 1, wx.TOP, 10)
        side_sizer.Add(self.spin, 1, wx.ALL, 5)

        # Run and Continue button
        side_sizer.Add(side_sizer1, 1, wx.ALL, 5)
        side_sizer1.Add(self.run_button, 1, wx.ALL, 5)
        side_sizer1.Add(self.continue_button, 1, wx.ALL, 5)

        # Switches
        if self.switch_ids:
            side_sizer.Add(self.text_switch_control, 1, wx.ALL, 10)
            side_sizer.Add(side_sizer2, 1, wx.ALL, 5)
            side_sizer2.Add(self.switch_choice, 1, wx.ALL, 5)
            side_sizer2.Add(self.switch_set, 1, wx.ALL, 5)

        # Monitor Add and Remove
        side_sizer.Add(self.text_monitor, 1, wx.ALL, 10)
        side_sizer.Add(side_sizer3, 1, wx.ALL, 5)
        side_sizer3.Add(self.add_monitor_choice, 1, wx.ALL, 5)
        side_sizer3.Add(self.add_monitor_button, 1, wx.ALL, 5)
        side_sizer.Add(side_sizer4, 1, wx.ALL, 5)
        side_sizer4.Add(self.remove_monitor_choice, 1, wx.ALL, 5)
        side_sizer4.Add(self.remove_monitor_button, 1, wx.ALL, 5)

        self.SetSizeHints(600, 600)
        self.SetSizer(main_sizer)

    def reset_screen(self):
        """Reset screen back to its intial size."""
        self.canvas.init = False
        # 2D
        self.canvas.pan_x = 0
        self.canvas.pan_y = 0
        self.canvas.zoom = 1
        # 3D
        self.canvas.scene_rotate = np.identity(4, 'f')

    def Toolbarhandler(self, event):
        """Handels toolbar presses."""
        if event.GetId() == self.QuitID:
            print("Quitting from Graphic User Interface.")
            print("Show help: logsim.py -h\n"
                  "Command line user interface: logsim.py -c <file path>\n"
                  "Graphical user interface: logsim.py <file path>")
            self.Close(True)
        if event.GetId() == self.OpenID:
            openFileDialog = wx.FileDialog(self, _("Open txt file"), "", "",
                                           wildcard="TXT files (*.txt)|*.txt",
                                           style=wx.FD_OPEN +
                                           wx.FD_FILE_MUST_EXIST)
            if openFileDialog.ShowModal() == wx.ID_CANCEL:
                print("The user cancelled the open-file action.")
                return
            new_path = openFileDialog.GetPath()
            print("File chosen is ", new_path)
            try:
                with open(new_path, 'r') as file:
                    content = file.read()
                    # Open the new window with the content
                    text_window = TextWindow(None, title=_('Definition File\
                                             Content'), content=content)
                    text_window.Show()
            except IOError:
                wx.LogError("Cannot open file '%s'." % new_path)

            # Initialise all the methods to analysis this file
            self.Close(True)
            names = Names()
            devices = Devices(names)
            network = Network(names, devices)
            monitors = Monitors(names, devices, network)
            scanner = Scanner(new_path, names)
            parser = Parser(names, devices, network, monitors, scanner)
            if parser.parse_network():
                gui = Gui("Logic Simulator", new_path, names, devices, network,
                          monitors)
                gui.Show(True)

        if event.GetId() == self.AboutID:
            wx.MessageBox("Logic Simulator\nTeam 3 - Sherry James Alex\n2024",
                          _("About Logsim"), wx.ICON_INFORMATION | wx.OK)

        if event.GetId() == self.HelpID:
            try:
                lang = os.getenv('LANG', 'en_UK').split('.')[0]
                if lang == 'zh_CN':
                    help_path = 'help_cn.png'
                else:
                    help_path = 'help_en.png'
                help_window = HelpWindow(None, title=_('Help'),
                                         image_path=help_path)
                help_window.Show()
            except IOError:
                wx.LogError("Cannot open file '%s'." % "help.png")

        # ~ if event.GetId() == self.HomeID:
            # ~ self.reset_screen()
            # ~ self.canvas.screen_type = (1, 0)
            # ~ self.canvas.render('')

        if event.GetId() == self.CubeID:
            self.reset_screen()
            if self.canvas.screen_type[0]:
                self.canvas.screen_type = (0, 1)
            else:
                self.canvas.screen_type = (1, 0)
            self.canvas.render('')

    def on_spin(self, event):
        """Handle the event when the user changes the spin control value."""
        spin_value = self.spin.GetValue()
        text = "".join(["New spin control value: ", str(spin_value)])
        self.canvas.render(text)

    def on_run_button(self, event):
        """Handle the event when the user clicks the run button."""
        spin_value = self.spin.GetValue()
        self.time_steps = spin_value
        self.run_network_and_get_values()
        text = "".join(["Run button pressed, time step is: ",
                        str(self.time_steps)])
        self.canvas.render(text)

    def on_continue_button(self, event):
        """Handle the event when the user clicks the continue button."""
        spin_cont_value = self.spin.GetValue()
        # self.time_steps += spin_cont_value
        # self.run_network_and_get_values()
        # Problem with continue button changes previous waveforms.
        self.current_steps = self.time_steps + spin_cont_value
        osc_here = False
        for i in range(self.time_steps, self.current_steps):
            if not self.network.execute_network():
                self.canvas.oscillating = True
                osc_here = True
            self.monitors.record_signals()
        if not osc_here:
            self.canvas.oscillating = False
        self.values = []
        monitor_dict = self.monitors.monitors_dictionary
        for device_id, output_id in monitor_dict:
            self.values.append(monitor_dict[(device_id, output_id)])
        self.trace_names = self.monitors.get_signal_names()[0]
        self.time_steps = self.current_steps

        text = "".join(["Continue button pressed, update time step: ",
                        str(self.time_steps)])
        self.canvas.render(text)

    def run_network_and_get_values(self):
        """Run the network and get the monitored signal values."""
        self.canvas.not_connected = not self.network.check_network()
        if self.canvas.not_connected:
            return ""
        self.devices.cold_startup()
        self.monitors.reset_monitors()

        osc_here = False
        for i in range(self.time_steps):
            if not self.network.execute_network():
                self.canvas.oscillating = True
                osc_here = True
            self.monitors.record_signals()
        if not osc_here:
            self.canvas.oscillating = False
        self.values = []

        monitor_dict = self.monitors.monitors_dictionary
        for device_id, output_id in monitor_dict:
            vals = monitor_dict[(device_id, output_id)]
            self.values.append(vals)
        self.trace_names = self.monitors.get_signal_names()[0]

    def on_text_box(self, event):
        """Handle the event when the user enters text."""
        text_box_value = self.text_box.GetValue()
        text = "".join(["New text box value: ", text_box_value])
        self.canvas.render(text)

    def on_switch_choice(self, event):
        """Handle the new_switch_choice event."""
        sw_name = self.switch_choice.GetValue()
        sw_val = self.switch_values[self.switch_names.index(sw_name)]
        if sw_val:
            self.switch_set.SetValue(1)
        else:
            self.switch_set.SetValue(0)

    def on_switch_set(self, event):
        """Handle the switch-set event."""
        sw_name = self.switch_choice.GetValue()
        sw_no = self.switch_names.index(sw_name)
        self.switch_values[sw_no] = [0, 1][self.switch_set.GetValue()]
        sw_id = self.names.query(sw_name)
        self.devices.set_switch(sw_id, self.switch_set.GetValue())
        # self.run_network_and_get_values()
        text = "".join(["Switch ", sw_name, " is now ",
                        "ON" if self.switch_values[sw_no] else "OFF"])
        self.canvas.render(text)

    def on_add_monitor_button(self, event):
        """User can add monitors using this button."""
        mon_choice_name = self.add_monitor_choice.GetValue()
        if '.' in mon_choice_name:
            dot_index = mon_choice_name.index('.')
            output_id = self.names.query(mon_choice_name[dot_index + 1:])
            mon_choice_name_start = mon_choice_name[:dot_index]
        else:
            mon_choice_name_start = mon_choice_name
            output_id = None

        if mon_choice_name not in self.sig_not_mons:
            return ''
        text = "".join(["Add monitor at ", str(mon_choice_name)])
        self.canvas.render(text)

        device_id = self.names.query(mon_choice_name_start)
        self.monitors.make_monitor(device_id, output_id)
        # self.run_network_and_get_values()

        self.sig_not_mons.remove(mon_choice_name)
        self.sig_mons.append(mon_choice_name)
        self.add_monitor_choice.SetItems(self.sig_not_mons)
        self.remove_monitor_choice.SetItems(self.sig_mons)
        if self.sig_not_mons:
            self.add_monitor_choice.SetValue(self.sig_not_mons[0])
        if self.sig_mons:
            self.remove_monitor_choice.SetValue(self.sig_mons[0])

    def on_remove_monitor_button(self, event):
        """User can remove monitors using this button."""
        mon_choice_name = self.remove_monitor_choice.GetValue()
        if '.' in mon_choice_name:
            dot_index = mon_choice_name.index('.')
            output_id = self.names.query(mon_choice_name[dot_index + 1:])
            mon_choice_name_strt = mon_choice_name[:dot_index]
        else:
            mon_choice_name_strt = mon_choice_name
            output_id = None

        if mon_choice_name not in self.sig_mons:
            return ''
        text = "".join(["Remove monitor at ", str(mon_choice_name)])
        self.canvas.render(text)

        device_id = self.names.query(mon_choice_name_strt)
        self.monitors.remove_monitor(device_id, output_id)
        # self.run_network_and_get_values()

        self.sig_not_mons.append(mon_choice_name)
        self.sig_mons.remove(mon_choice_name)

        self.add_monitor_choice.SetItems(self.sig_not_mons)
        self.remove_monitor_choice.SetItems(self.sig_mons)
        if self.sig_not_mons:
            self.add_monitor_choice.SetValue(self.sig_not_mons[0])
        if self.sig_mons:
            self.remove_monitor_choice.SetValue(self.sig_mons[0])


# This window would appear when the user choose to open a TXT file.
# This window would show the entire content of the TXT file.
class TextWindow(wx.Frame):

    def __init__(self, parent, title, content):
        super(TextWindow, self).__init__(parent, title=title)

        # Set up the new window
        panel = wx.Panel(self)
        text_ctrl = wx.TextCtrl(panel, value=content,
                                style=wx.TE_MULTILINE | wx.TE_READONLY,
                                pos=(10, 10), size=(380, 550))

        self.SetTitle(title)
        self.SetSize((400, 600))


# This window would appear when the user click Help button.
# The graphic user guide would pop up.
class HelpWindow(wx.Frame):
    def __init__(self, parent, title, image_path):
        super(HelpWindow, self).__init__(parent, title=title)

        # Set up the new window
        panel = wx.Panel(self)

        # Load the image
        image = wx.Image(image_path, wx.BITMAP_TYPE_PNG)

        # Define the maximum size for the window
        max_width, max_height = 800, 600

        # Scale the image if it's larger than the maximum size
        img_width, img_height = image.GetWidth(), image.GetHeight()

        if img_width > max_width or img_height > max_height:
            scaling_factor = min(max_width / img_width,
                                 max_height / img_height)
            new_width = int(img_width * scaling_factor)
            new_height = int(img_height * scaling_factor)
            image = image.Scale(new_width, new_height, wx.IMAGE_QUALITY_HIGH)

        bitmap = wx.StaticBitmap(panel, -1, wx.Bitmap(image), pos=(10, 10))

        self.SetTitle(title)

        # Adjust window size to fit the image
        self.SetSize((bitmap.GetSize()[0] + 20, bitmap.GetSize()[1] + 40))
