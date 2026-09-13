#version 430
layout(location = 0) in vec2 pos;

void main() {
    // convert from grid coords to NDC
    gl_Position = vec4((pos / vec2(1000, 1000)) * 2.0 - 1.0, 0.0, 1.0);
}