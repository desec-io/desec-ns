function signal(signaling_domain, qtype)
    -- determine signal type
    prefix = qname:getRawLabels()[1]

    -- obtain signals
    local signals = {}
    if prefix == '_dsboot' and qname:getRawLabels()[2] ~= '_dsboot' then  -- 2nd cond. forbids nested signaling names
        qname:chopOff()
        signals = resolve(qname:makeRelative(newDN(signaling_domain)):toString(), qtype)
    end

    -- return signals
    local ret = {}
    for k, v in pairs(signals) do
        table.insert(ret, v:toString())
    end
    return ret
end
