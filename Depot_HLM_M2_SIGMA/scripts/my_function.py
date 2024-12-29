### From Hugo C. I don't use the field name here its only binary 
def hugo(in_vector, ref_image, out_image, field_name=None, dtype=None):
    """
    See otbcli_rasterisation for details on parameters
    """
    if field_name is None:
        # Mode binaire si field_name est None
        cmd_pattern = (
            "otbcli_Rasterization -in {in_vector} -im {ref_image} -out {out_image} -mode binary"
        )
        cmd = cmd_pattern.format(in_vector=in_vector, ref_image=ref_image, out_image=out_image)
    else:
        # Mode attribut si field_name est spécifié
        if dtype is not None:
            field_name = field_name + ' ' + dtype
        cmd_pattern = (
            "otbcli_Rasterization -in {in_vector} -im {ref_image} -out {out_image}"
            " -mode attribute -mode.attribute.field {field_name}"
        )
        cmd = cmd_pattern.format(in_vector=in_vector, ref_image=ref_image,
                                 out_image=out_image, field_name=field_name)
    print(cmd)
    
    # pour python >= 3.7
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        print(result.decode())
    except subprocess.CalledProcessError as e:
        print("Erreur lors de l'exécution de la commande :")
        print(e.output.decode())
    except FileNotFoundError:
        print("La commande 'otbcli_Rasterization' est introuvable. Assurez-vous qu'OTB est installé.")
###