def benchmark():
    try:
        st = time.perf_counter()
        n, ops = 123456789, 0
        deadline = st + 1.2
        while time.perf_counter() < deadline:
            n = (n * 1103515245 + 12345) & 0x7FFFFFFF
            n ^= n >> 13
            ops += 1
        cpu_ops = ops / max(time.perf_counter() - st, 0.001)
        sz = 512 * 1024
        try:
            a, b = bytearray(sz), bytearray(sz)
            st2 = time.perf_counter()
            tb = 0
            deadline2 = st2 + 0.5
            while time.perf_counter() < deadline2:
                b[:] = a
                a[0] = (a[0]+1)%256
                tb += sz*2
            mem_mb = (tb/(1024*1024)) / max(time.perf_counter()-st2, 0.001)
        except:
            mem_mb = 200.0
        return cpu_ops, mem_mb
    except:
        return 50_000_000.0, 200.0
