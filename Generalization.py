def generalization(element):
    # todo 有点特殊化了
    if len(element.getElementsByTagName("generalization")) != 0 and \
            len(element.getElementsByTagName("referenceExtension")) != 0:
        general = (element.getElementsByTagName("referenceExtension")[0])
        type = general.getAttribute("referentPath").split("Profile::")[1]
        return type
    else:
        return None
