#version 460 core
layout(local_size_x = 16, local_size_y = 16) in;
layout(rgba32f, binding = 0) uniform image2D img_output;

layout(std430, binding = 1) buffer rx
{
    float data[];
};

layout(std430, binding = 2) buffer rb
{
    float r[];
};

layout(std430, binding = 3) buffer gb
{
    float g[];
};

layout(std430, binding = 4) buffer tb
{
    float b[];
};

uniform float maximum = 1.0f;
uniform float minimum = 0.0f;
uniform int stride;
uniform int dimX;
uniform int dimY;



void main() {
    //if(gl_GlobalInvocationID.x > dimX || gl_GlobalInvocationID.y > dimY )return;
    if(gl_GlobalInvocationID.x >= 1900) return;
    if(gl_GlobalInvocationID.y >= 1000) return;
    uint index = gl_GlobalInvocationID.x + gl_GlobalInvocationID.y * stride;
    float value = float(gl_GlobalInvocationID.y);
    //vec4 color = vec4(r[index], g[index], b[index], 1.0f);
    vec4 color = vec4(r[index], g[index], b[index], 1.0f);
    imageStore(img_output, ivec2(gl_GlobalInvocationID.xy), color); // white
}