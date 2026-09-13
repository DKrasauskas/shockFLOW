#version 330 core
#define SMOOTH 0

out vec4 FragColor;
in vec3 pos;

uniform sampler2D tex;
uniform float zoom;
uniform float x;
uniform float y;

void main()
{
    vec2 norm = (pos.xy + 1.0f) * 0.5f;
    // pivot around texture center (0.5, 0.5)
   vec2 center = vec2(0, 0);
//d
//    // apply zoom
    vec2 zoomed = (norm - vec2(0.5, 0.5))  * zoom - center;
    FragColor = texture(tex, norm);

    //FragColor = vec4(1, 1, 1, 1);

}