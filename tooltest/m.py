from manim import *
config.pixel_width=1080;config.pixel_height=1920;config.frame_rate=30;config.frame_width=9;config.frame_height=16
class T(Scene):
    def construct(self):
        c=Circle(2,color=ORANGE);t=Text("lyrebird",font="Kalam").shift(DOWN*3)
        self.play(Create(c),run_time=2);self.play(Write(t),c.animate.scale(0.5),run_time=2);self.wait(1)
