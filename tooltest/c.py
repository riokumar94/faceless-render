import cairo,subprocess,math
W,H=1080,1920;p=subprocess.Popen(f"ffmpeg -v error -y -f rawvideo -pix_fmt bgra -s {W}x{H} -r 30 -i - -c:v libx264 -crf 18 -pix_fmt yuv420p cairo5s.mp4".split(),stdin=subprocess.PIPE)
s=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H)
for f in range(150):
    c=cairo.Context(s);c.set_source_rgb(.95,.92,.84);c.paint();c.set_line_width(8);c.set_source_rgb(.2,.15,.1)
    c.arc(540,960,300,0,2*math.pi*f/150);c.stroke();c.select_font_face("Kalam");c.set_font_size(90);c.move_to(300,1500);c.show_text("frame %d"%f)
    p.stdin.write(s.get_data())
p.stdin.close();p.wait()
