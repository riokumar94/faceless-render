import asyncio,subprocess
from playwright.async_api import async_playwright
HTML="""<html><body style='margin:0'><canvas id=c width=1080 height=1920></canvas><script>
const x=document.getElementById('c').getContext('2d');window.draw=f=>{x.fillStyle='#f3ead7';x.fillRect(0,0,1080,1920);x.lineWidth=8;x.beginPath();x.arc(540,960,300,0,2*Math.PI*f/150);x.stroke();x.font='90px Kalam';x.fillStyle='#222';x.fillText('frame '+f,300,1500)}</script></body></html>"""
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--headless=new']);pg=await b.new_page(viewport={'width':1080,'height':1920});await pg.set_content(HTML)
    ff=subprocess.Popen("ffmpeg -v error -y -f image2pipe -framerate 30 -i - -c:v libx264 -crf 18 -pix_fmt yuv420p html5s.mp4".split(),stdin=subprocess.PIPE)
    for f in range(150):
      await pg.evaluate(f"draw({f})");ff.stdin.write(await pg.screenshot(type='png'))
    ff.stdin.close();ff.wait();await b.close()
asyncio.run(main())
