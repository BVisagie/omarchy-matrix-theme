// Optional Ghostty effect. Static, with no flicker, warping or cursor trails.
// Sample neighboring light without recoloring errors or selection highlights.
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 px = 1.0 / iResolution.xy;
    vec4 source = texture(iChannel0, uv);
    vec3 halo = vec3(0.0);
    halo += texture(iChannel0, clamp(uv + vec2(px.x, 0.0), vec2(0.0), vec2(1.0))).rgb;
    halo += texture(iChannel0, clamp(uv - vec2(px.x, 0.0), vec2(0.0), vec2(1.0))).rgb;
    halo += texture(iChannel0, clamp(uv + vec2(0.0, px.y), vec2(0.0), vec2(1.0))).rgb;
    halo += texture(iChannel0, clamp(uv - vec2(0.0, px.y), vec2(0.0), vec2(1.0))).rgb;
    halo = max(halo * 0.25 - vec3(0.12), vec3(0.0));
    fragColor = vec4(min(source.rgb + halo * 0.09, vec3(1.0)), source.a);
}
