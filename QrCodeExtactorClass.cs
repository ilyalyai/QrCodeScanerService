/// <summary>
/// Генерация изображения из текста
/// </summary>
/// <param name="qrText">Текст внутри кода</param>
/// <param name="useRTCColors">Использовать цвета логотипа РТК</param>
/// <param name="pathToFile">Путь, по которому сохранить изображение. Сохраняем только если он предоставлен</param>
/// <param name="damageLevelCorrection">Уровень коррекции ошибок (от 0 до 3). По умолчанию 2</param>
/// <returns></returns>
public static byte[] AddQrCode(string qrText, bool useRTCColors, string pathToFile = "",  int damageLevelCorrection = 0)
{
    byte[] blackColor = useRTCColors ? new byte[] { 184, 153, 91, 255 } : new byte[] { 0, 0, 0, 255 };
    return AddQrCode(qrText, pathToFile, damageLevelCorrection, blackColor, new byte[] { 255, 255, 255, 255 });
}

/// <summary>
/// Генерация изображения из текста
/// </summary>
/// <param name="qrText">Текст внутри кода</param>
/// <param name="pathToFile">Путь, по которому сохранить изображение. Сохраняем только если он предоставлен</param>
/// <param name="damageLevelCorrection">Уровень коррекции ошибок (от 0 до 3). По умолчанию 2</param>
/// <param name="blackColor">Массив byte RGBA черного цвета кода. По умолчанию берется черный</param>
/// <param name="whiteColor">Массив byte RGBA белого цвета кода. По умолчанию берется белый</param>
/// <returns>QR код в виде байтовогом массива</returns>
public static byte[] AddQrCode(string qrText, string pathToFile = "", int damageLevelCorrection = 0, byte[] blackColor = null, byte[] whiteColor = null)
{
    if (blackColor == null)
        blackColor = new byte[] { 0, 0, 0, 255 };
    if (whiteColor == null)
        whiteColor = new byte[] { 255, 255, 255, 255 };
    //интересный факт - после тестов определил, что лучше всего коды определяются при коррекции = 1 или 2
    //На 3 видимо слишком получается мелкий код, а на 0 наоборот недостаточно инфы получается
    if (damageLevelCorrection < 0 || damageLevelCorrection > 3)
        damageLevelCorrection = 2;
    using (QRCodeGenerator qrGenerator = new QRCodeGenerator())
    using (QRCodeData qrCodeData = qrGenerator.CreateQrCode(qrText, (QRCodeGenerator.ECCLevel)damageLevelCorrection))
    using (PngByteQRCode qrCode = new PngByteQRCode(qrCodeData))
    {
        byte[] qrCodeImage = qrCode.GetGraphic(10, blackColor, whiteColor);
        if (!string.IsNullOrEmpty(pathToFile))
            File.WriteAllBytes(Path.Combine(pathToFile, "qrCode.png"), qrCodeImage);
        return qrCodeImage;
    }
}

public static string ExtractQrCode(string filePath, int pageNum)
{
    if (string.IsNullOrEmpty(filePath) || !File.Exists(filePath) || pageNum < 0)
        return null;

    return QrCodeExtactor.GetTextFromDocument(filePath, pageNum);
}

private static class QrCodeExtactor
{
    private static readonly HttpClient _client = new();

    public static string GetTextFromDocument(string filePath, int pageNum)
    {
        byte[] imageBytes = null;
        if (filePath.ToLower().EndsWith(".pdf"))
            imageBytes = ConvertToImage(filePath, pageNum);
        else
        {
            Image img = Image.FromFile(filePath);
            if (img == null)
                return null;
            using (MemoryStream ms = new MemoryStream())
            {
                img.Save(ms, img.RawFormat);
                imageBytes = ms.ToArray();
            }
        }
        return GetTextFromQrCode(imageBytes);
    }

    private static byte[] ConvertToImage(string filePath, int pageNumber)
    {
        var response = SendPdfToConverter(filePath, pageNumber);
        if (response.StatusCode == System.Net.HttpStatusCode.BadRequest)
        {
            throw new Exception(response.Content.ReadAsStringAsync().Result);
        }
        else if (response.StatusCode == System.Net.HttpStatusCode.InternalServerError)
        {
            throw new Exception("Произошла внутренняя ошибка сервиса конвертации PDF в JPEG.");
        }

        return response.Content.ReadAsByteArrayAsync().Result;
    }

    private static HttpResponseMessage SendPdfToConverter(string filePath, int pageNumer)
    {
        string boundary = "----" + DateTime.Now.Ticks.ToString("x");
        var fs = new FileStream(filePath, FileMode.Open, FileAccess.Read);
        if (fs.Length == 0)
        {
            throw new InvalidOperationException("Файл пустой.");
        }
        using MultipartFormDataContent form = new(boundary)
        {
            { new StreamContent(fs), "document", "document.pdf" },
            { new StringContent(pageNumer.ToString()), "page_number" }
        };
        string url = Service.GetRegistryValue<string>(@"Server\QrCodeServiceApi\ApiImageFromDocumentUrl", User.System, @"http://192.168.201.99:8002/convert-to-jpeg");
        HttpRequestMessage message = new(HttpMethod.Post, url)
        {
            Content = form
        };
        try
        {
            return _client.SendAsync(message).Result;
        }
        catch (HttpRequestException ex)
        {
            throw new("Сервис для конвертирования PDF в JPEG не доступен!", ex);
        }
        finally
        {
            fs.Dispose();
        }
    }

    private static string GetTextFromQrCode(byte[] image)
    {
        string url = Service.GetRegistryValue<string>(@"Server\QrCodeServiceApi\QrCodeServiceApiUrl", User.System, @"http://192.168.201.99:8003/scan_for_qr_code");

        HttpRequestMessage message = new(HttpMethod.Post, url)
        {
            Content = new ByteArrayContent(image)
        };

        HttpResponseMessage response = new(System.Net.HttpStatusCode.InternalServerError);
        try
        {
            response = _client.SendAsync(message).Result;
        }
        catch (HttpRequestException ex)
        {
            throw new("Модель для распознавания текста не доступна!", ex);
        }

        if (response.StatusCode == System.Net.HttpStatusCode.BadRequest)
        {
            throw new HttpListenerException((int)response.StatusCode, response.Content.ReadAsStringAsync().Result);
        }

        return response.Content.ReadAsStringAsync().Result;
    }
}