#version 460 core
layout(location = 0) in vec3 aPos;
out vec3 pos;

void main() {
    gl_Position = vec4(aPos.x * 2, aPos.y * 2 , 0, 1.0);
    pos = vec3(aPos.x * 2 , aPos.y * 2, 0);/// color_map(lininterp(data[gl_VertexID]));
}
